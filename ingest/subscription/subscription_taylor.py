import re

import numpy as np
import pandas as pd

from app import db
from ingest.subscription.subscription_base import SubscriptionImport
from ingest.utils import get_or_create
from models.journal import Journal
from models.price import MiniBundle, SubscriptionPrice


class TaylorFrancis(SubscriptionImport):
    """
    Takes an Excel File of Taylor Francis prices and adds them into the database.
    """

    def __init__(self, year):
        """
        Loads Taylor Francis specific data into a Publisher class.
        """
        self.data_source = "https://taylorandfrancis.com/journals/price-lists/"
        currencies_and_regions = {
            "USD": "USA",
            "GBP": "GBR",
            "EUR": "EUR",
            "USD - ROW": "ROW",
            "AUD": "AUS",
            "CAD": "CAN",
        }
        regions_and_currencies = [
            ("USA", "USD"),
            ("GBR", "GBP"),
            ("EUR", "EUR"),
            ("ROW", "USD"),
            ("AUS", "AUD"),
            ("CAN", "CAD"),
        ]
        publisher_name = "Taylor & Francis"
        super().__init__(
            year,
            currencies_and_regions,
            regions_and_currencies,
            publisher_name,
        )

    def format_tf_dataframe(self, file_path):
        """
        Loads the Taylor Francis Price List into a parsable dataframe.
        """
        xls = pd.ExcelFile(file_path)
        df = pd.read_excel(xls, "2021 Prices")
        df.replace("", np.nan, inplace=True)
        # Make all online versions end in ' online'
        df["Journal Name "] = df["Journal Name "].str.replace(
            "( online| Online| \WOnline\W | \Wonline\W)", " online", regex=True
        )
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df = df[df["Journal Name "].notna()]
        # Filter out non-online versions when an online version is present, otherwise keep the print version
        vals = df.loc[
            df["Journal Name "].str.contains(" online"), "Journal Name "
        ].str.replace(" online", "")
        df = df[~df["Journal Name "].isin(vals)]
        self.df = df

    def import_prices(self):
        """
        Iterate through the dataframe and import the Sage Price List into the
        SubscriptionPrice model.
        """
        temp = dict(self.currencies_and_regions)
        for index, row in self.df.iterrows():
            self.set_journal_name(row["Journal Name "])
            self.set_issn(row["ISSN"])
            self.set_journal()
            self.set_currency(row["Currency"])
            if not self.currency:
                continue
            cur = self.get_raw_currency(row["Currency"])
            region = temp[cur]
            self.set_region(region)
            self.set_country(region)
            self.process_fte(row["Price Group"])
            self.set_price(row["2021 rate"])
            self.add_price_to_db()

        db.session.commit()

    def get_raw_currency(self, cell):
        if pd.isnull(cell):
            return None
        else:
            return cell

    def process_fte(self, cell):
        """
        Parses the "Price Group" column from the Taylor and Francis price sheet and returns
        the fte_from and fte_to values.
        """
        fte_data = cell.split()
        fte_data = [data for data in fte_data if data.isdigit()]

        if len(fte_data) == 3:  # 1 - 9 999
            self.fte_from = int(fte_data[0])
            self.fte_to = int(fte_data[1] + fte_data[2])

        elif len(fte_data) == 4:  # 10 000 - 19 999 ... 40 000 - 49 999
            self.fte_from = int(fte_data[0] + fte_data[1])
            self.fte_to = int(fte_data[2] + fte_data[3])

        elif len(fte_data) == 2:  # 50 000 and over
            self.fte_from = int(fte_data[0] + fte_data[1])
            self.fte_to = self.MAX_FTE

        else:
            self.fte_from = None
            self.fte_to = None


class TaylorMiniBundle(SubscriptionImport):
    """
    Iterates through taylor francis spreadsheet to find mini bundles.
    """

    def __init__(self, year):
        publisher_name = "Taylor & Francis"
        currencies_and_regions = {
            "USD": "USA",
            "GBP": "GBR",
            "EUR": "EUR",
            "USD - ROW": "ROW",
            "AUD": "AUS",
            "CAD": "CAN",
        }
        regions_and_currencies = [
            ("USA", "USD"),
            ("GBR", "GBP"),
            ("EUR", "EUR"),
            ("ROW", "USD"),
            ("AUS", "AUD"),
            ("CAN", "CAD"),
        ]
        super().__init__(
            year, currencies_and_regions, regions_and_currencies, publisher_name
        )
        self.mini_bundle_name = None
        self.issns = []

    def format_tf_dataframe(self, file_path):
        """
        Loads the Taylor Francis Price List into a parsable dataframe.
        """
        xls = pd.ExcelFile(file_path)
        df = pd.read_excel(xls, "2021 Prices")
        df.replace("", np.nan, inplace=True)
        # Make all online versions end in ' online'
        df["Journal Name "] = df["Journal Name "].str.replace(
            "( online| Online| \WOnline\W | \Wonline\W)", " online", regex=True
        )
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df = df[df["Journal Name "].notna()]
        # Filter out non-online versions when an online version is present, otherwise keep the print version
        vals = df.loc[
            df["Journal Name "].str.contains(" online"), "Journal Name "
        ].str.replace(" online", "")
        df = df[~df["Journal Name "].isin(vals)]
        self.df = df

    def set_mini_bundle_name(self, cell):
        """
        Sets the mini bundle name given a dataframe cell
        """
        if not pd.isnull(cell):
            self.mini_bundle_name = cell
            self.mini_bundle_name = self.mini_bundle_name.replace("Online", "").replace(
                "online", ""
            )
            self.mini_bundle_name = self.mini_bundle_name.strip()

    def set_issns(self, cell):
        if not pd.isnull(cell):
            issns = re.findall(r"\w{4}-\w{4}", cell)
            [self.issns.append(issn) for issn in issns]

    def import_prices(self):
        """
        Iterate through the dataframe and import the Sage Price List into the
        SubscriptionPrice model.
        """
        temp = dict(self.currencies_and_regions)
        for index, row in self.df.iterrows():
            self.set_mini_bundle_name(row["Journal Name "])
            self.set_issns(row["ISSN"])
            self.set_currency(row["Currency"])
            if not self.currency:
                continue
            cur = self.get_raw_currency(row["Currency"])
            region = temp[cur]
            self.set_region(region)
            self.set_country(region)
            self.set_price(row["2021 rate"])
            self.add_prices()

            # reset for next loop
            self.issns = []
        db.session.commit()

    def get_raw_currency(self, cell):
        if pd.isnull(cell):
            return None
        else:
            return cell

    def add_prices(self):
        if (
            len(self.issns) > 1
            and self.price
            and "1750-2837" not in self.issns
            and "1750-7812" not in self.issns
        ):
            self.add_price_to_db()

    def add_price_to_db(self):
        """
        Adds a SubscriptionPrice entry into the database.
        """
        mb = get_or_create(
            db.session,
            MiniBundle,
            name=self.mini_bundle_name,
            publisher_id=self.publisher.id,
        )

        # create price if it does not exist
        currency = self.currency
        country = self.country
        region = self.current_region
        price_found = False

        for p in mb.subscription_prices:
            if (
                p.price == self.price
                and p.country == country
                and p.currency == currency
                and p.region == region
            ):
                print(
                    "Price already exists for mini bundle {} with price {}".format(
                        self.mini_bundle_name, self.price
                    )
                )
                price_found = True

        if not price_found:
            new_price = SubscriptionPrice(
                price=self.price,
                country=country,
                currency=currency,
                region=region,
                year=self.year,
            )
            db.session.add(new_price)
            # match price to mini bundle
            mb.subscription_prices.append(new_price)
            print(
                "Adding price {} {} to mini bundle {}".format(
                    self.price, self.currency.acronym, self.mini_bundle_name
                )
            )
            db.session.commit()

        # assign journals to mini bundle
        for issn in self.issns:
            j = Journal.find_by_issn(issn)
            if j and j not in mb.journals:
                print(
                    "assigning journal with issn {} to mini bundle {}".format(
                        j.issn_l, self.mini_bundle_name
                    )
                )
                mb.journals.append(j)
            elif j:
                print(
                    "Journal with issn {} already assigned to mini bundle {}".format(
                        j.issn_l, self.mini_bundle_name
                    )
                )
            else:
                print("Journal does not exist for issn {}".format(issn))

        db.session.commit()

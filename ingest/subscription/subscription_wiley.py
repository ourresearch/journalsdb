import regex as re

import pandas as pd
from sqlalchemy import func

from app import db
from models.journal import Journal
from models.price import MiniBundle, SubscriptionPrice
from ingest.subscription.subscription_base import SubscriptionImport
from ingest.utils import get_or_create


class Wiley(SubscriptionImport):
    def __init__(self, year):
        self.journal_info = None
        self.media_type = None
        self.material_number = None
        self.electronic_mediums = ["Online"]
        self.online_found = False
        self.data_source = (
            "https://onlinelibrary.wiley.com/library-info/products/price-lists"
        )
        regions_and_currencies = [
            ("USA", "USD"),
            ("UK", "GBP"),
            ("Europe", "EUR"),
            ("Rest of World", "USD"),
        ]
        publisher_names = "Wiley"
        super().__init__(year, None, regions_and_currencies, publisher_names)

    def format_wb_dataframe(self, excel_file_path):
        """
        The Wiley Blackwell spreadsheet has difficult formatting to work with. This
        reorganizes the spreadsheet to use appropriate column headers and renames some
        columns to make it easier to parse data.
        """
        xls = pd.ExcelFile(excel_file_path)
        df = pd.read_excel(xls, "Wiley Price List")
        new_header = df.iloc[0]
        df = df[1:]
        df.columns = new_header
        df.rename(
            columns={
                "Journal Title\nAcronym\nPrint ISSN\nVol & issues": "Journal_Info"
            },
            inplace=True,
        )
        df.rename(columns={"Nan": "Product_Group"})
        self.df = df

    def import_wiley_blackwell(self):
        """
        Iterates through a dataframe containing pricing information and saves this information
        into the database.
        """
        for index, row in self.df.iterrows():

            self.set_journal_info(row["Journal_Info"])

            if self.journal_info and "_____" in self.journal_info:
                self.reset_journal_data()
                continue

            self.set_journal_name()
            self.set_media_type(row["Media"])
            self.set_issn(row["Journal_Info"])

            if self.issn and self.journal_name and self.media_type:
                self.set_product_id(row["Material Number"])
                self.set_journal()
                self.set_fte_range()

                for region, currency_acronym in self.regions_and_currencies:
                    self.set_price(row[region])
                    self.set_currency(currency_acronym)
                    self.set_region(region)
                    self.set_country(region)
                    self.add_price_to_db()

        db.session.commit()

    def reset_journal_data(self):
        """
        When an underline is found within the spreadsheet, it indicates the current
        journal prices have concluded and prices for a new journal will start.

        Sets all journal related variables to None, so the new journal can be ingested
        """
        self.journal_name = None
        self.journal_info = None
        self.product_group = None
        self.issn = None
        self.volume_info = None
        self.online_found = False

    def set_journal_info(self, cell):
        """
        The Journal Info cell may contain the title, acronym, issn, Vol & Issues, FTE, and
        other miscellaneous data. Updates journal_info to whichever is contained within
        the cell.
        """
        if pd.isnull(cell):
            self.journal_info = None
        else:
            self.journal_info = str(cell)

    def set_journal_name(self):
        """
        After an underline has been encountered in the spreadsheet a new journal has started.
        Once the first non-null entry in the Journal Info column is found, it should be set
        to the journal_name.
        """
        if self.journal_info and not self.journal_name:
            self.journal_name = self.journal_info

    def set_media_type(self, cell):
        """
        Media types could contain "Print & Online", "Online", "Print" or an unrelated string.
        Only 'Online' mediums should be added to the database. If an online medium does not exist,
        print should be added.
        """
        if pd.isnull(cell):
            self.media_type = None
        elif cell == "Online":
            self.media_type = cell
            self.online_found = True
        elif cell == "Print" and not self.online_found:
            self.media_type = cell
            print("Online pricing does not exist: ", self.issn)
        else:
            self.media_type = None
            print("Online found or Print&Online:", self.issn)

    def set_issn(self, cell):
        """
        Sets the ISSN for a Journal given a dataframe cell. If the cell is not an ISSN,
        sets ISSN to None.
        """
        if self.is_issn(cell) and not self.issn:
            self.issn = cell.strip()

    def is_issn(self, cell):
        """
        ISSNs are codes formatted as XXXX-XXXX where X can be a character or integer.
        Returns True if the provided string matches ISSN format.
        """
        issn_as_str = str(cell)
        if re.match(r"^\s?\w{4}-\w{4}\s?\s?$", issn_as_str):
            return True
        return False

    def set_fte_range(self):
        """
        Wiley Blackwell occasionally has different prices based on Full-Time Employee status.
        This checks to see if an FTE group (SMALL, MEDIUM, LARGE) is specified in the material
        number. Returns the fte_from and fte_to values if they exist.
        """

        if "SMALL" in self.product_id:
            self.fte_from, self.fte_to = 1, 10000

        elif "MEDIUM" in self.product_id:
            self.fte_from, self.fte_to = 100001, 40000

        elif "LARGE" in self.product_id:
            self.fte_from, self.fte_to = 40001, self.MAX_FTE

        else:
            self.fte_from, self.fte_to = None, None


class WileyMiniBundle(SubscriptionImport):
    def __init__(self, year):
        self.data_source = (
            "https://onlinelibrary.wiley.com/library-info/products/price-lists"
        )
        self.includes = None
        self.journal_info = None
        self.journals = []
        self.media_type = None
        self.mini_bundle_name = None
        self.online_found = False

        regions_and_currencies = [
            ("USA", "USD"),
            ("UK", "GBP"),
            ("Europe", "EUR"),
            ("Rest of World", "USD"),
        ]
        publisher_names = "Wiley"
        super().__init__(year, None, regions_and_currencies, publisher_names)

    def import_wiley_mini_bundles(self):
        """
        Iterates through a dataframe containing pricing information and saves this information
        into the database.
        """

        for index, row in self.df.iterrows():
            self.set_journal_info(row["Journal_Info"])
            self.set_mini_bundle_name()
            if self.journal_info and "includes" in self.journal_info.lower():
                # list of journals we want to add to mini_bundle
                self.set_included_journals()

            if self.journal_info and "_____" in self.journal_info:
                # at the end of current journal data so need to reset
                self.reset_journal_data()
                continue

            if self.mini_bundle_name and self.journals:
                self.set_media_type(row["Media"])

                if self.media_type == "Online":
                    for region, currency_acronym in self.regions_and_currencies:
                        self.set_price(row[region])
                        self.set_currency(currency_acronym)
                        self.set_region(region)
                        self.set_country(region)
                        self.add_price_to_db()

            db.session.commit()

    def format_wb_dataframe(self, excel_file_path):
        """
        The Wiley Blackwell spreadsheet has difficult formatting to work with. This
        reorganizes the spreadsheet to use appropriate column headers and renames some
        columns to make it easier to parse data.
        """
        xls = pd.ExcelFile(excel_file_path)
        df = pd.read_excel(xls, "Wiley Price List")
        new_header = df.iloc[0]
        df = df[1:]
        df.columns = new_header
        df.rename(
            columns={
                "Journal Title\nAcronym\nPrint ISSN\nVol & issues": "Journal_Info"
            },
            inplace=True,
        )
        df.rename(columns={"Nan": "Product_Group"})
        self.df = df

    def set_journal_info(self, cell):
        """
        The Journal Info cell may contain the title, acronym, issn, Vol & Issues, FTE, and
        other miscellaneous data. Updates journal_info to whichever is contained within
        the cell.
        """
        if pd.isnull(cell):
            self.journal_info = None
        else:
            self.journal_info = str(cell)

    def set_mini_bundle_name(self):
        if (
            self.journal_info
            and not re.match(r"^\s?\w{4}-\w{4}\s?\s?$", str(self.journal_info))
            and "package" in self.journal_info.lower()
            and "also available" not in self.journal_info.lower()
        ):
            self.mini_bundle_name = self.journal_info.strip()

    def set_included_journals(self):
        self.includes = self.journal_info.replace("Includes", "").split(",")
        self.includes = [title.replace(".", "").strip() for title in self.includes]
        for title in self.includes:
            j = Journal.query.filter(
                func.lower(Journal.title) == func.lower(title)
            ).first()
            if j:
                self.journals.append(j)
            else:
                print(title, "not found in included titles")

    def reset_journal_data(self):
        """
        When an underline is found within the spreadsheet, it indicates the current
        journal prices have concluded and prices for a new journal will start.

        Sets all journal related variables to None, so the new journal can be ingested
        """
        self.journal_info = None
        self.mini_bundle_name = None
        self.journals.clear()
        self.product_group = None
        self.includes = None
        self.online_found = False

    def set_media_type(self, cell):
        """
        Media types could contain "Print & Online", "Online", "Print" or an unrelated string.
        Only 'Online' mediums should be added to the database. If an online medium does not exist,
        print should be added.
        """
        if pd.isnull(cell):
            self.media_type = None
        elif cell == "Online":
            self.media_type = cell
            self.online_found = True
        elif cell == "Print" and not self.online_found:
            self.media_type = cell
            print("Online pricing does not exist: ", self.issn)

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
        price_found = False
        for p in mb.subscription_prices:
            if (
                p.price == self.price
                and p.country == country
                and p.currency == currency
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
        for j in self.journals:
            if j not in mb.journals:
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

        db.session.commit()

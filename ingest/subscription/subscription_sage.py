import pandas as pd

from app import db
import regex as re
from models.journal import Journal
from models.location import Region
from models.price import MiniBundle, SubscriptionPrice
from ingest.subscription.subscription_base import SubscriptionImport
from ingest.utils import get_or_create


class Sage(SubscriptionImport):

    """
    Takes a CSV of sage prices and adds them into the database.
    """

    def __init__(self, year):
        self.data_source = (
            "https://us.sagepub.com/en-us/nam/sage-journals-and-subscription-info"
        )
        regions_and_currencies = [("USA", "USD"), ("GBR", "GBP")]
        super().__init__(
            year,
            None,
            regions_and_currencies,
            "SAGE",
        )
        self.in_electronic_price = True

    def format_sage_dataframe(self, excel_file_path):
        """
        Loads the Sage Price List into a parsable dataframe.
        """
        xls = pd.ExcelFile(excel_file_path)
        self.df = pd.read_excel(xls, "List Price")

    def set_issn(self, cell):
        if (
            pd.isnull(cell)
            or not isinstance(cell, str)
            or not re.match(r"^\s?\w{4}-\w{4}\s?\s?$", cell)
        ):
            self.issn = None
        else:
            self.issn = cell.split(",")[0].strip()

    def import_prices(self):
        """
        Iterate through the dataframe and import the Sage Price List into the
        SubscriptionPrice model.
        """
        for index, row in self.df.iterrows():
            self.set_journal_name(row["Title"])
            self.set_issn(row["E-ISSN"])
            self.set_journal()
            self.set_product_id(row["Product"])
            self.in_electronic_price = False
            for region, currency_acronym in self.regions_and_currencies:
                self.set_currency(currency_acronym)
                self.set_country(region)
                column = currency_acronym + " Price " + str(self.year)
                self.set_price(row[column])
                media_type = row["Product Description"]
                price_category = row["Price Category Description"]
                self.add_prices(media_type, price_category)
        db.session.commit()

    def add_prices(self, media_type, price_category):
        if (
            self.journal
            and media_type == "Electronic Only"
            and price_category == "Inst-Standard"
        ):
            self.add_price_to_db()
            self.in_electronic_price = True

    def set_region(self, region):
        """
        Queries the region from the database and sets this as a class variable.
        """
        try:
            self.current_region = (
                db.session.query(Region)
                .filter_by(name=region, publisher_id=self.publisher.id)
                .first()
            )
        except:
            print("Could not find region:", region)


class SageMiniBundle(SubscriptionImport):

    """
    Takes a CSV of sage mini bundle prices and adds them into the database.
    """

    def __init__(self, year):
        regions_and_currencies = [("USA", "USD"), ("GBR", "GBP")]
        super().__init__(
            year,
            None,
            regions_and_currencies,
            "SAGE",
        )
        self.mini_bundle_name = None
        self.issns = []
        self.in_electronic_price = True

    def format_sage_dataframe(self, excel_file_path):
        """
        Loads the Sage Price List into a parsable dataframe.
        """
        xls = pd.ExcelFile(excel_file_path)
        self.df = pd.read_excel(xls, "List Price")

    def set_mini_bundle_name(self, cell):
        """
        Sets the mini bundle name given a dataframe cell
        """
        if not pd.isnull(cell):
            self.mini_bundle_name = cell

    def set_issns(self, cell):
        cell = cell if cell else ""
        issns = re.findall(r"\w{4}-\w{4}", cell)
        [self.issns.append(issn) for issn in issns]

    def import_prices(self):
        """
        Iterate through the dataframe and import the Sage Price List into the
        SubscriptionPrice model.
        """
        for index, row in self.df.iterrows():
            self.set_mini_bundle_name(row["Title"])
            self.set_issns(row["E-ISSN"])
            self.set_product_id(row["Product"])
            self.in_electronic_price = False
            for region, currency_acronym in self.regions_and_currencies:
                self.set_currency(currency_acronym)
                self.set_country(region)
                column = currency_acronym + " Price " + str(self.year)
                self.set_price(row[column])
                media_type = row["Product Description"]
                price_category = row["Price Category Description"]
                self.add_prices(media_type, price_category)
            self.issns = []
        db.session.commit()

    def add_prices(self, media_type, price_category):
        if (
            len(self.issns) > 1
            and media_type == "Electronic Only"
            and price_category == "Inst-Standard"
            and self.price
        ):
            self.add_price_to_db()
            self.in_electronic_price = True

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

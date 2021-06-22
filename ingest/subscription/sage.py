import pandas as pd

from app import db
import regex as re
from models.location import Region
from models.price import SubscriptionPrice
from ingest.subscription.subscription_import import SubscriptionImport


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
        elif (
            self.journal
            and media_type == "Electronic Only"
            and price_category != "Inst-Standard"
        ):
            self.remove_price_from_journal()

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

    def remove_price_from_journal(self):
        """
        Removes price if it is not inst-standard.
        """
        if self.journal and self.price:

            if self.country_id:
                entries = self.get_country_entries()
            else:
                entries = self.get_region_entries()

            existing_entries = [
                e for e in entries if e in self.journal.subscription_prices
            ]  # find any existing price that may be matched to the journal
            entry = existing_entries[0] if existing_entries else None

            if entry:
                self.journal.subscription_prices.remove(entry)
                print(
                    "Removed SubscriptionPrice: ",
                    entry.price,
                    " from Journal: ",
                    self.journal.issn_l,
                )
                db.session.commit()

        else:
            print("Nothing to remove: ", self.journal.issn_l)

import pandas as pd

from app import db
from models.location import Region
from ingest.subscription_import import SubscriptionImport


class Sage(SubscriptionImport):

    """
    Takes a CSV of sage prices and adds them into the database.
    """

    def __init__(self, year):
        self.year = int(year)
        regions_and_currencies = [("USA", "USD"), ("GBR", "GBP")]
        super().__init__(year, None, regions_and_currencies, "SAGE Publications")

    def format_sage_dataframe(self, excel_file_path):
        """
        Loads the Sage Price List into a parsable dataframe.
        """
        xls = pd.ExcelFile(excel_file_path)
        self.df = pd.read_excel(xls, "List Price")

    def import_prices(self):
        """
        Iterate through the dataframe and import the Sage Price List into the
        SubscriptionPrice model.
        """
        for index, row in self.df.iterrows():
            if self.is_electronic(row["Product Description"]):
                self.set_journal_name(row["Title"])
                self.set_issn(row["E-ISSN"])
                self.set_journal()
                self.set_product_id(row["Product"])
                for region, currency_acronym in self.regions_and_currencies:
                    self.set_currency(currency_acronym)
                    self.set_region(region)
                    self.set_country()
                    column = currency_acronym + " Price " + str(self.year)
                    self.set_price(row[column])
                    media_type = row["Product Description"]
                    self.add_prices(media_type)
        db.session.commit()

    def add_prices(self, media_type):
        if self.journal:
            if media_type == "Electronic Only":
                self.journal.subscription_prices = []
                db.session.commit()
                self.add_price_to_db()
            else:
                if len(self.journal.subscription_prices) == 0:
                    self.add_price_to_db()

    def is_electronic(self, cell):
        """
        Returns True if the medium is Electronic.
        """
        if not pd.isnull(cell):
            if cell.lower().find("electronic") > -1:
                return True

        return False

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

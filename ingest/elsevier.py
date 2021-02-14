import pandas as pd

from app import db
from ingest.subscription_import import SubscriptionImport
from models.location import Region


class Elsevier(SubscriptionImport):
    def __init__(self, year):
        regions_and_currencies = {
            "USA": "USD",
            "Canada": "USD",
            "Mexico": "USD",
            "Rest of World": "USD",
        }
        super().__init__(year, None, regions_and_currencies, "Elsevier ")

    def format_elsevier_dataframe(self, excel_file_path):
        """
        Loads the Elsevier Price List into a parsable dataframe.
        """
        df = pd.read_excel(excel_file_path)
        self.df = df

    def set_region(self, region):
        """
        Finds the Region model entry for a given region.
        """
        try:
            self.current_region = (
                db.session.query(Region).filter_by(name=region).first()
            )
        except:
            print("Could not find region associated with country")

    def import_elsevier_prices(self):
        """
        Parses the Elsevier Subscription Prices CSV and adds SubscriptionPrice data into the
        database.

        Elsevier's quirk is the price columns which are all in USD despite different countries/
        regions.

        USA - USD
        Canada - USD
        Mexico - USD
        Rest of World - USD
        """
        for index, row in self.df.iterrows():
            self.set_journal_name(row["Journal Title"])
            self.set_issn(row["ISSN"])
            self.set_journal()
            for region, currency_acronym in self.regions_and_currencies.items():
                self.set_currency(currency_acronym)
                self.set_region(region)
                column = region + " - " + currency_acronym
                self.set_price(row[column])
                if self.price:
                    self.add_price_to_db()

        db.session.commit()

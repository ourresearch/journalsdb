import pandas as pd

from app import db
from ingest.subscription_import import SubscriptionImport
from models.location import Region


class Elsevier(SubscriptionImport):
    def __init__(self, year):
        self.data_source = "https://www.elsevier.com/books-and-journals/journal-pricing/print-price-list"
        super().__init__(year, None, None, "Elsevier ")
        self.regions_and_currencies = [
            ("USA", "USD"),
            ("Canada", "USD"),
            ("Mexico", "USD"),
            ("Rest of World", "USD"),
            ("Japan", "YEN"),
            ("Japan", "USD"),
            ("Europe", "EUR"),
            ("France", "EUR"),
            ("UK", "GBP"),
            ("Europe", "USD"),
            ("D, A, CH", "EUR"),
        ]
        self.countries = set(["USA", "Canada", "Mexico", "Japan", "France", "UK"])

    def format_elsevier_dataframe(self, excel_file_path):
        """
        Loads the Elsevier Price List into a parsable dataframe.
        """
        df = pd.read_excel(excel_file_path)
        self.df = df
        to_remove = []
        for region, currency_acronym in self.regions_and_currencies:
            column = region + " - " + currency_acronym
            if column not in df.columns:
                to_remove.append((region, currency_acronym))
        for pair in to_remove:
            self.regions_and_currencies.remove(pair)

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
            self.set_product_id(row["Journal No."])
            for region, currency_acronym in self.regions_and_currencies:
                self.set_currency(currency_acronym)
                self.set_region(region)
                self.set_country(region)
                column = region + " - " + currency_acronym
                self.set_price(row[column])
                if self.price:
                    self.add_price_to_db()

        db.session.commit()

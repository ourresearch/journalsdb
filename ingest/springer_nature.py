import pandas as pd
import numpy as np

from app import db
from ingest.subscription_import import SubscriptionImport
from models.location import Region


class SpringerNature(SubscriptionImport):
    def __init__(self, year):
        self.year = int(year)
        regions_and_currencies = [("USA", "USD")]
        super().__init__(
            year,
            None,
            regions_and_currencies,
            "Springer Science and Business Media LLC",
        )

    def format_springer_dataframe(self, file_path):
        """
        Loads the Springer Nature Price List into a parsable dataframe.
        """
        xls = pd.ExcelFile(file_path)
        df = pd.read_excel(xls, "SN Journals USD Price List 2021", header=5)
        df.replace("", np.nan, inplace=True)
        self.df = df

    def set_region(self):
        """
        Finds the Region model entry for a given country.
        """
        try:
            self.current_region = (
                db.session.query(Region)
                .filter_by(name="USA", publisher_id=self.publisher.id)
                .first()
            )
        except:
            print("Could not find region associated with country")

    def import_prices(self):
        """
        Parses the Springer Nature Price List and adds entries to Database
        """
        self.set_currency("USD")
        self.set_region()
        self.set_country()
        for index, row in self.df.iterrows():
            self.set_journal_name(row["Title"])
            self.set_issn(row["ISSN electronic"])
            self.set_journal()
            self.set_product_id(row["Product ID"])
            self.set_price(row["Institutional Price electronic only USD"])
            self.add_price_to_db()

        db.session.commit()

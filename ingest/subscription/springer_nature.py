import pandas as pd
import numpy as np

from app import db
from ingest.subscription.subscription_import import SubscriptionImport
from models.location import Country


class SpringerNature(SubscriptionImport):
    def __init__(self, year):
        self.data_source = "https://www.springernature.com/gp/librarians/licensing/journals-catalog/journal-price-lists"
        regions_and_currencies = [("USA", "USD")]
        publisher_name = "Springer Nature"
        super().__init__(
            year,
            None,
            regions_and_currencies,
            publisher_name,
        )

    def format_springer_dataframe(self, file_path):
        """
        Loads the Springer Nature Price List into a parsable dataframe.
        """
        xls = pd.ExcelFile(file_path)
        df = pd.read_excel(xls, "SN Journals USD Price List 2021", header=5)
        df.replace("", np.nan, inplace=True)
        self.df = df

    def set_country(self):
        """
        Gets a country given the provided acronym
        """
        self.country = None
        self.country_id = None
        if not self.current_region:
            self.country = (
                db.session.query(Country)
                .filter_by(name="United States of America")
                .first()
            )
            if self.country:
                self.country_id = self.country.id
            else:
                print("No country for region:", self.country)

    def import_prices(self):
        """
        Parses the Springer Nature Price List and adds entries to Database
        """
        self.set_currency("USD")
        self.set_country()
        for index, row in self.df.iterrows():
            self.set_journal_name(row["Title"])
            self.set_issn(row["ISSN electronic"])
            self.set_journal()
            self.set_product_id(row["Product ID"])
            self.set_price(row["Institutional Price electronic only USD"])
            self.add_price_to_db()

        db.session.commit()

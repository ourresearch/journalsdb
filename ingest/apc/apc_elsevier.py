import pandas as pd
from ingest.apc.apc_import import ImportAPC


class ElsevierAPC(ImportAPC):
    """
    Imports the APC pricing for Elsevier

    Spreadsheet: https://www.elsevier.com/books-and-journals/journal-pricing/apc-pricelist
    """

    def __init__(self, year):
        self.data_source = (
            "https://www.elsevier.com/books-and-journals/journal-pricing/apc-pricelist"
        )
        publisher_names = [
            "Elsevier - Academic Press",
            "Elsevier - WB Saunders",
            "Elsevier - Mosby",
            "Elsevier - CIG Media Group LP",
            "Elsevier - International Federation of Automatic Control (IFAC)",
            "Elsevier - Medicine Publishing Company",
            "Elsevier - Wilderness Medical Society",
            "Elsevier- Churchill Livingstone",
            "Elsevier",
        ]
        super().__init__(year, publisher_names)
        self.currencies = set(["USD", "EUR", "GBP", "JPY"])
        self.currency_to_country = {
            "USD": "USA",
            "EUR": None,
            "GBP": "GBR",
            "JPY": "JPN",
        }
        self.currency_to_region = {
            "EUR": "EUR",
        }

    def parse_excel(self, file):
        """
        Removes leading rows and moves headers down to align with currency
        values.
        """
        xls = pd.ExcelFile(file)
        df = pd.read_excel(xls, header=2)
        df.iat[0, 0] = "ISSN"
        df.iat[0, 1] = "Title"
        df.iat[0, 2] = "Business Model"
        new_header = df.iloc[0]
        df = df[1:]
        df.columns = new_header
        self.df = df

    def import_prices(self):
        for index, row in self.df.iterrows():
            self.set_issn(row["ISSN"])
            self.set_journal()
            if self.row["issn-l"]:
                for acronym in self.currencies:
                    self.set_currency_id(acronym)
                    self.set_country_id(acronym)
                    self.set_region_id(acronym)
                    self.set_price(row[acronym])
                    self.save_price()

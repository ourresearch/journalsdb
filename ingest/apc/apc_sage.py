import pandas as pd
from ingest.apc.apc_import import ImportAPC


class SageAPC(ImportAPC):
    def __init__(self, year):
        self.data_source = "Journal home page description"
        publisher_names = [
            "SAGE Publications",
        ]
        super().__init__(year, publisher_names)
        self.currencies = set(["USD", "GBP"])
        self.currency_to_country = {
            "USD": "USA",
            "GBP": "GBR",
            "INR": "IND",
        }
        self.currency_to_region = None

    def parse_excel(self, file):
        df = pd.read_csv(file)
        df = df[df["apc_amount"].notna()]
        self.df = df

    def import_prices(self):
        for index, row in self.df.iterrows():
            self.set_issn(row["issn-l"])
            self.set_journal()
            if self.row["issn-l"]:
                self.set_currency_id(row["apc_currency"])
                self.set_country_id(row["apc_currency"])
                self.set_region_id(row["apc_currency"])
                self.set_price(row["apc_amount"])
                self.save_price()

    def set_region_id(self, currency_acronym):
        """
        Looks for a Region based on currency acronym and adds the ID to the APC data.
        """
        self.row["region_id"] = None

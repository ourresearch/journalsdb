import pandas as pd
from ingest.apc.apc_base import ImportAPC


class SpringerAPC(ImportAPC):
    def __init__(self, year):
        self.data_source = (
            "https://www.springernature.com/gp/open-research/journals-books/journals"
        )
        publisher_names = [
            "Springer-Verlag",
            "Springer (Biomed Central Ltd.)",
            "Springer - Global Science Journals",
            "Springer - Psychonomic Society",
            "Springer (Kluwer Academic Publishers)",
            "Springer Fachmedien Wiesbaden GmbH",
            "Springer - RILEM Publishing",
            "Springer Publishing Company",
            "Springer - Society of Surgical Oncology",
            "Springer - Adis",
            "Springer - Humana Press",
            "Springer Science and Business Media LLC",
        ]
        super().__init__(year, publisher_names)
        self.currencies = set(["USD", "EUR", "GBP"])
        self.currency_to_country = {
            "USD": "USA",
            "EUR": None,
            "GBP": "GBR",
        }
        self.currency_to_region = {"EUR": "EUR"}

    def parse_excel(self, file, is_hybrid):
        """
        Loads an Excel File as a dataframe
        """
        xls = pd.ExcelFile(file)
        if is_hybrid:
            self.is_hybrid = True
            self.format_hybrid(xls)
        else:
            self.is_hybrid = False
            self.format_open(xls)

    def format_hybrid(self, xls):
        df = pd.read_excel(xls, header=3)
        df.columns = [
            "Journal Title",
            "Journal ID",
            "ISSN",
            "Imprint",
            "Open Access Type",
            "License",
            "Language",
            "EUR",
            "USD",
            "GBP",
        ]
        self.df = df

    def format_open(self, xls):
        df = pd.read_excel(xls, header=4)
        df.columns = [
            "Journal Title",
            "Journal ID",
            "ISSN",
            "License",
            "Language",
            "EUR",
            "USD",
            "GBP",
            "website",
        ]
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

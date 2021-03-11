import pandas as pd
from ingest.apc.apc_import import ImportAPC


class WileyAPC(ImportAPC):
    def __init__(self, year):
        self.data_source = "https://authorservices.wiley.com/author-resources/Journal-Authors/open-access/article-publication-charges.html"
        super().__init__(year, "Wiley (Blackwell Publishing)")
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
        """
        Hybrid and Open Access have different formats.
        This assigns the correct columns for hybrid and
        removes symbols from currencies
        """
        df = pd.read_excel(xls, header=4)
        df.iat[0, 0] = "Online ISSN"
        df.iat[0, 1] = "Journal"
        df.iat[0, 2] = "USD"
        df.iat[0, 3] = "GBP"
        df.iat[0, 4] = "EUR"
        df.iat[0, 5] = "USD"
        df.iat[0, 6] = "GBP"
        df.iat[0, 7] = "EUR"
        self.set_header(df)

    def format_open(self, xls):
        """
        Hybrid and Open Access have different formats.
        This assigns the correct columns for open access
        """
        df = pd.read_excel(xls, header=3)
        df.iat[0, 0] = "Journal"
        df.iat[0, 1] = "Online ISSN"
        df.iat[0, 2] = "Licenses"
        df.iat[0, 15] = "APC Notes"
        self.set_header(df)

    def set_header(self, df):
        """
        Sets the dataframe header as the first row
        """
        new_header = df.iloc[0]
        df = df[1:]
        df.columns = new_header
        self.df = df

    def narrow_dataframe(self, cols_to_keep):
        """
        Wiley has four column groups for Pricing

        - Full Price
        - Referral Price
        - Society Membership 1
        - Society Membership 2

        This narrows the columns down to one group.

        cols_to_keep: List of integers
        """
        column_numbers = [x for x in range(self.df.shape[1])]
        cols_to_remove = [n for n in column_numbers if n not in cols_to_keep]
        full_price_cols = self.remove_cols(column_numbers, cols_to_remove)
        self.df = self.df.iloc[:, full_price_cols]

    def remove_cols(self, column_numbers, cols_to_remove):
        """
        Removes integers from a list of column numbers
        """
        for n in cols_to_remove:
            column_numbers.remove(n)
        return column_numbers

    def import_prices(self):
        for index, row in self.df.iterrows():
            self.set_issn(row["Online ISSN"])
            self.set_journal()
            if self.row["issn-l"]:
                for acronym in self.currencies:
                    self.set_currency_id(acronym)
                    self.set_country_id(acronym)
                    self.set_region_id(acronym)
                    self.set_price(row[acronym])
                    if not self.is_hybrid:
                        self.set_notes(row["APC Notes"])
                    self.save_price()

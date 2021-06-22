import regex as re

import pandas as pd

from app import db
from ingest.subscription.subscription_import import SubscriptionImport


class WileyBlackwell(SubscriptionImport):
    def __init__(self, year):
        self.journal_info = None
        self.media_type = None
        self.material_number = None
        self.electronic_mediums = ["Online"]
        self.online_found = False
        self.data_source = (
            "https://onlinelibrary.wiley.com/library-info/products/price-lists"
        )
        regions_and_currencies = [
            ("USA", "USD"),
            ("UK", "GBP"),
            ("Europe", "EUR"),
            ("Rest of World", "USD"),
        ]
        publisher_names = "Wiley"
        super().__init__(year, None, regions_and_currencies, publisher_names)

    def format_wb_dataframe(self, excel_file_path):
        """
        The Wiley Blackwell spreadsheet has difficult formatting to work with. This
        reorganizes the spreadsheet to use appropriate column headers and renames some
        columns to make it easier to parse data.
        """
        xls = pd.ExcelFile(excel_file_path)
        df = pd.read_excel(xls, "Wiley Price List")
        new_header = df.iloc[0]
        df = df[1:]
        df.columns = new_header
        df.rename(
            columns={
                "Journal Title\nAcronym\nPrint ISSN\nVol & issues": "Journal_Info"
            },
            inplace=True,
        )
        df.rename(columns={"Nan": "Product_Group"})
        self.df = df

    def import_wiley_blackwell(self):
        """
        Iterates through a dataframe containing pricing information and saves this information
        into the database.
        """
        for index, row in self.df.iterrows():

            self.set_journal_info(row["Journal_Info"])

            if self.journal_info and "_____" in self.journal_info:
                self.reset_journal_data()
                continue

            self.set_journal_name()
            self.set_media_type(row["Media"])
            self.set_issn(row["Journal_Info"])

            if self.issn and self.journal_name and self.media_type:
                self.set_product_id(row["Material Number"])
                self.set_journal()
                self.set_fte_range()

                for region, currency_acronym in self.regions_and_currencies:
                    self.set_price(row[region])
                    self.set_currency(currency_acronym)
                    self.set_region(region)
                    self.set_country(region)
                    self.add_price_to_db()

        db.session.commit()

    def reset_journal_data(self):
        """
        When an underline is found within the spreadsheet, it indicates the current
        journal prices have concluded and prices for a new journal will start.

        Sets all journal related variables to None, so the new journal can be ingested
        """
        self.journal_name = None
        self.journal_info = None
        self.product_group = None
        self.issn = None
        self.volume_info = None
        self.online_found = False

    def set_journal_info(self, cell):
        """
        The Journal Info cell may contain the title, acronym, issn, Vol & Issues, FTE, and
        other miscellaneous data. Updates journal_info to whichever is contained within
        the cell.
        """
        if pd.isnull(cell):
            self.journal_info = None
        else:
            self.journal_info = str(cell)

    def set_journal_name(self):
        """
        After an underline has been encountered in the spreadsheet a new journal has started.
        Once the first non-null entry in the Journal Info column is found, it should be set
        to the journal_name.
        """
        if self.journal_info and not self.journal_name:
            self.journal_name = self.journal_info

    def set_media_type(self, cell):
        """
        Media types could contain "Print & Online", "Online", "Print" or an unrelated string.
        Only 'Online' mediums should be added to the database. If an online medium does not exist,
        print should be added.
        """
        if pd.isnull(cell):
            self.media_type = None
        elif cell == "Online":
            self.media_type = cell
            self.online_found = True
        elif cell == "Print" and not self.online_found:
            self.media_type = cell
            print("Online pricing does not exist: ", self.issn)
        else:
            self.media_type = None
            print("Online found or Print&Online:", self.issn)

    def set_issn(self, cell):
        """
        Sets the ISSN for a Journal given a dataframe cell. If the cell is not an ISSN,
        sets ISSN to None.
        """
        if self.is_issn(cell) and not self.issn:
            self.issn = cell.strip()

    def is_issn(self, cell):
        """
        ISSNs are codes formatted as XXXX-XXXX where X can be a character or integer.
        Returns True if the provided string matches ISSN format.
        """
        issn_as_str = str(cell)
        if re.match(r"^\s?\w{4}-\w{4}\s?\s?$", issn_as_str):
            return True
        return False

    def set_fte_range(self):
        """
        Wiley Blackwell occasionally has different prices based on Full-Time Employee status.
        This checks to see if an FTE group (SMALL, MEDIUM, LARGE) is specified in the material
        number. Returns the fte_from and fte_to values if they exist.
        """

        if "SMALL" in self.product_id:
            self.fte_from, self.fte_to = 1, 10000

        elif "MEDIUM" in self.product_id:
            self.fte_from, self.fte_to = 100001, 40000

        elif "LARGE" in self.product_id:
            self.fte_from, self.fte_to = 40001, self.MAX_FTE

        else:
            self.fte_from, self.fte_to = None, None

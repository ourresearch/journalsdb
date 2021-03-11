import pandas as pd
from app import db
from models.journal import Journal, Publisher
from models.location import Country, Region
from models.price import APCPrice, Currency
import regex as re


class ImportAPC:
    """
    Base class for importing APC Pricing for various publishers.
    """

    def __init__(self, year, publisher):
        self.data_source = None
        self.row = {}
        self.row["note"] = None
        self.df = None
        self.year = int(year)
        self.publisher = None
        self.set_publisher(publisher)

    def set_publisher(self, name):
        """
        Loads the publisher model from the database
        """
        self.publisher = db.session.query(Publisher).filter_by(name=name).first()
        if self.publisher and not self.publisher.apc_data_source:
            breakpoint()
            self.publisher.apc_data_source = self.data_source
            db.session.commit()

    def set_issn(self, cell):
        """
        Sets the ISSN-L given a dataframe cell
        """
        if pd.isnull(cell):
            self.row["issn-l"] = None
        else:
            self.row["issn-l"] = cell

    def set_journal(self):
        """
        Sets the journal given a dataframe cell
        """
        issn_l = self.row["issn-l"]
        self.journal = None
        if issn_l:
            journal = db.session.query(Journal).filter_by(issn_l=issn_l).first()
            self.journal = journal

    def set_currency_id(self, currency_acronym):
        """
        Looks for a currency based on currency acronym and adds the ID to the APC data.
        """
        self.row["currency_id"] = None
        try:
            currency = (
                db.session.query(Currency).filter_by(acronym=currency_acronym).first()
            )
            self.row["currency_id"] = currency.id
        except:
            print("Currency missing from database: ", currency_acronym)

    def set_region_id(self, currency_acronym):
        """
        Looks for a Region based on currency acronym and adds the ID to the APC data.
        """
        self.row["region_id"] = None
        if currency_acronym in self.currency_to_region:
            region_name = self.currency_to_region[currency_acronym]

            try:
                region = db.session.query(Region).filter_by(name=region_name).first()
                self.row["region_id"] = region.id
            except:
                print("Region missing from database: ", region_name)

    def set_country_id(self, currency_acronym):
        """
        Looks for a country based on currency acronym and adds the ID to the APC data.
        """
        self.row["country_id"] = None
        country_acronym = self.currency_to_country[currency_acronym]
        if country_acronym:

            try:
                country = (
                    db.session.query(Country).filter_by(iso3=country_acronym).first()
                )
                self.row["country_id"] = country.id
            except:
                print("Country missing from database: ", country_acronym)

    def set_price(self, cell):
        """
        Prices should be in the format '$XXXX.XX' or 'XXXXX'. This grabs all
        decimal values or integers from the price cell.
        """
        self.row["price"] = None
        if not pd.isnull(cell):
            price_as_str = str(cell)
            price_as_str.replace(",", "")
            price = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", price_as_str))
            if price != "":
                self.row["price"] = float(price)

    def set_notes(self, cell):
        """
        Adds Notes column
        """
        self.row["note"] = None
        if not pd.isnull(cell):
            self.row["note"] = cell

    def save_price(self):
        """
        Adds an APC price to the database.
        """
        if self.row["price"]:
            print(self.row["price"])
            print(self.row["issn-l"])
            entry = (
                db.session.query(APCPrice)
                .filter_by(
                    price=self.row["price"],
                    currency_id=self.row["currency_id"],
                    country_id=self.row["country_id"],
                    region_id=self.row["region_id"],
                    year=self.year,
                    notes=self.row["note"],
                )
                .first()
            )

            if entry:
                print("Entry Exists")

            if not entry:
                print("Creating new price entry")

                entry = APCPrice(
                    price=self.row["price"],
                    currency_id=self.row["currency_id"],
                    country_id=self.row["country_id"],
                    region_id=self.row["region_id"],
                    year=self.year,
                    notes=self.row["note"],
                )

                db.session.add(entry)
                db.session.commit()

            if self.journal:
                if entry not in self.journal.apc_prices:
                    print("Adding price to journal: ", entry.price, self.journal.issn_l)
                    self.journal.apc_prices.append(entry)
                    db.session.commit()
                else:
                    print("Price already added to Journal")

            else:
                print("No Journal for ISSN: ", self.row["issn-l"])

import regex as re

import pandas as pd

from app import db
from models.journal import Journal, Publisher
from models.location import Country, Region
from models.price import SubscriptionPrice, Currency


class SubscriptionImport:
    """
    Class that supports publisher subscription spreadsheet imports.
    """

    def __init__(
        self,
        year,
        currencies_and_regions=None,
        regions_and_currencies=None,
        publisher=None,
    ):
        self.df = None
        self.year = int(year)
        self.journal = None
        self.journal_name = None
        self.issn = None
        self.product_id = None
        self.MAX_FTE = 1000000
        self.fte_from = 1
        self.fte_to = self.MAX_FTE
        self.price = None
        self.currencies_and_regions = currencies_and_regions
        self.regions_and_currencies = regions_and_currencies
        self.publisher = None
        self.set_publisher(publisher)
        self.current_region = None
        self.currency = None
        self.country = None

    def set_publisher(self, name):
        """
        Loads the publisher model from the database
        """
        self.publisher = db.session.query(Publisher).filter_by(name=name).first()

    def add_regions_to_db(self):
        """
        Adds all publisher regions to the database if they do not already exist.
        """
        for r in self.regions_and_currencies.keys():
            exists = (
                db.session.query(Region)
                .filter_by(name=r, publisher_id=self.publisher.id)
                .first()
            )
            if not exists:
                try:
                    region = Region(name=r, publisher_id=self.publisher.id)
                    db.session.add(region)
                    db.session.flush()
                except:
                    print("Could not add region to database")
        db.session.commit()

    def set_journal_name(self, cell):
        """
        Sets the journal name given a dataframe cell
        """
        if pd.isnull(cell):
            self.journal_name = None
        else:
            self.journal_name = cell

    def set_issn(self, cell):
        """
        Sets the issn given a dataframe cell
        """
        if (
            pd.isnull(cell)
            or not isinstance(cell, str)
            or not re.match(r"^\w{4}-\w{4}$", cell)
        ):
            self.issn = None
        else:
            self.issn = cell

    def set_journal(self):
        """
        Sets the Journal given an ISSN
        """
        self.journal = Journal.find_by_issn(self.issn)

    def set_currency(self, acronym):
        """
        Takes a currency acronym (example 'USD') and finds the associated entry in the database.
        Returns the entry or None if not found.
        """
        if pd.isnull(acronym):
            self.currency = (
                db.session.query(Currency).filter_by(acronym="Unknown").first()
            )

        else:
            if acronym == "USD - ROW":
                acronym = "USD"

            self.currency = (
                db.session.query(Currency).filter_by(acronym=acronym).first()
            )

            if not self.currency:
                print("Currency Associated with " + acronym + " not found")

    def set_country(self, cell):
        """
        Gets a country given the provided currency acronym (or None for "Rest of World")
        """
        if (
            pd.isnull(cell)
            or cell == "USD - ROW"
            or cell == "EUR"
            or cell != "Rest of World"
        ):
            self.country = None
        else:
            acronym = self.currencies_and_regions[cell]
            self.country = db.session.query(Country).filter_by(iso3=acronym).first()

    def set_region(self):
        """
        Finds the Region model entry for a given region.
        """
        if self.currency.acronym == "EUR":
            acronym = "EUR"
        elif self.currency.acronym == "ROW":
            acronym = "ROW"
        else:
            acronym = self.currencies_and_regions[self.currency.acronym]
        self.current_region = (
            db.session.query(Region)
            .filter_by(name=acronym, publisher_id=self.publisher.id)
            .first()
        )

    def set_price(self, cell):
        """
        Prices should be in the format '$XXXX.XX' or 'XXXXX'. This grabs all decimal values or
        integers from the price cell.
        """
        if pd.isnull(cell):
            self.price = None
        else:
            price_as_str = str(cell)
            price_as_str.replace(",", "")
            price = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", price_as_str))
            if price != "":
                self.price = float(price)
            else:
                self.price = None

    def add_price_to_db(self):
        """
        Adds a SubscriptionPrice entry into the database.
        """
        if self.journal and self.price:
            entry = (
                db.session.query(SubscriptionPrice)
                .filter_by(
                    price=self.price,
                    currency_id=self.currency.id,
                    region_id=self.current_region.id,
                    fte_from=self.fte_from,
                    fte_to=self.fte_to,
                    year=self.year,
                )
                .first()
            )

            if not entry or entry not in self.journal.subscription_prices:

                try:
                    price_entry = SubscriptionPrice(
                        price=self.price,
                        currency_id=self.currency.id,
                        region_id=self.current_region.id,
                        fte_from=self.fte_from,
                        fte_to=self.fte_to,
                        year=self.year,
                    )

                    db.session.add(price_entry)
                    self.journal.subscription_prices.append(price_entry)
                    db.session.flush()

                    print(
                        "Added SubscriptionPrice: ",
                        price_entry.price,
                        " to Journal: ",
                        self.journal.issn_l,
                    )

                except:
                    print(
                        "Failed to add SubscriptionPrice from Journal",
                        self.journal.issn_l,
                    )

            else:
                print("Price already in database: ", self.journal.title)
        else:
            print("Could not add price due to missing journal entry:", self.issn)
import regex as re

import pandas as pd

from app import db
from models.journal import Journal, Publisher
from models.location import Country, Region
from models.price import SubscriptionPrice, Currency
import datetime


class SubscriptionImport:
    """
    Class that supports publisher subscription spreadsheet imports.
    """

    def __init__(
        self,
        year,
        currencies_and_regions=None,
        regions_and_currencies=None,
        publisher_name=None,
    ):
        self.df = None
        self.year = int(year)
        self.journal = None
        self.journal_name = None
        self.issn = None
        self.product_id = None
        self.MAX_FTE = 1000000
        self.fte_from = None
        self.fte_to = None
        self.price = None
        self.currencies_and_regions = currencies_and_regions
        self.regions_and_currencies = regions_and_currencies
        self.publisher = None
        self.set_publisher(publisher_name)
        self.current_region = None
        self.currency = None
        self.country = None
        self.country_id = None
        self.regions_to_countries = {
            "France": "France, French Republic",
            "Japan": "Japan",
            "UK": "United Kingdom of Great Britain & Northern Ireland",
            "USA": "United States of America",
            "Mexico": "Mexico, United Mexican States",
            "Canada": "Canada",
            "AUS": "Australia, Commonwealth of",
            "GBR": "United Kingdom of Great Britain & Northern Ireland",
        }
        self.countries = set(
            ["USA", "Canada", "Mexico", "Japan", "France", "UK", "AUS", "GBR"]
        )

    def set_publisher(self, name):
        """
        Loads the publisher model from the database
        """
        self.publisher = db.session.query(Publisher).filter_by(name=name).first()
        if self.publisher and not self.publisher.sub_data_source:
            self.publisher.sub_data_source = self.data_source
        db.session.commit()

    def add_regions_to_db(self):
        """
        Adds all publisher regions to the database if they do not already exist.
        """
        for r, c in self.regions_and_currencies:
            exists = (
                db.session.query(Region)
                .filter_by(name=r, publisher_id=self.publisher.id)
                .first()
            )
            if not exists:
                try:
                    region = Region(
                        name=r,
                        publisher_id=self.publisher.id,
                        created_at=datetime.datetime.now(),
                    )
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
            or not re.match(r"^\s?\w{4}-\w{4}\s?\s?$", cell)
        ):
            self.issn = None
        else:
            self.issn = cell.strip()

    def set_journal(self):
        """
        Sets the Journal given an ISSN
        """
        self.journal = Journal.find_by_issn(self.issn)

    def set_product_id(self, cell):
        """
        Each publisher has a unique internal ID to represent the journal. This needs to
        be added to the database in the journal model.
        """
        if pd.isnull(cell):
            self.product_id = None
        else:
            self.product_id = str(cell)

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

            elif acronym == "YEN":
                acronym = "JPY"

            self.currency = (
                db.session.query(Currency).filter_by(acronym=acronym).first()
            )

            if not self.currency:
                print("Currency Associated with " + acronym + " not found")

    def set_country(self, region):
        """
        Gets a country given the provided acronym (or None for "Rest of World")
        """
        self.country = None
        self.country_id = None
        if not self.current_region:
            self.country = (
                db.session.query(Country)
                .filter_by(name=self.regions_to_countries[region])
                .first()
            )
            if self.country:
                self.country_id = self.country.id
            else:
                print("No country for region:", region)

    def set_region(self, region):
        """
        Finds the Region model entry for a given region.
        """
        self.current_region = None
        if region not in self.countries:
            try:
                self.current_region = (
                    db.session.query(Region).filter_by(name=region).first()
                )
            except:
                print("Region missing from DB: ", region)

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

        Prices should only include a region or a country, but not both. If a country exists
        it should be added without a region. Regions consist of many countries, so there
        is no need to specify a specific country.
        """
        if self.journal and isinstance(self.price, (int, float)):
            if self.country_id:
                entries = self.get_country_entries()
            else:
                entries = self.get_region_entries()

            existing_entries = [
                e for e in entries if e in self.journal.subscription_prices
            ]  # find any existing price that may be matched to the journal
            entry = entries[0] if entries else None

            if not existing_entries and not entry:

                # create new entry
                entry = SubscriptionPrice(
                    price=self.price,
                    currency_id=self.currency.id,
                    fte_from=self.fte_from,
                    fte_to=self.fte_to,
                    year=self.year,
                    created_at=datetime.datetime.now(),
                )
                if self.country_id:
                    entry.country_id = self.country_id
                    entry.region_id = None
                else:
                    entry.country_id = None
                    entry.region_id = self.current_region.id

                try:
                    db.session.add(entry)
                    db.session.flush()
                except:
                    print(
                        "Failed to add SubscriptionPrice from Journal",
                        self.journal.issn_l,
                    )

            if not existing_entries and entry not in self.journal.subscription_prices:
                # attach entry object to journal subscription_prices
                self.journal.subscription_prices = self.journal.subscription_prices[
                    :
                ] + [entry]
                self.journal.internal_publisher_id = self.product_id
                db.session.commit()
                print(
                    "Added SubscriptionPrice: ",
                    entry.price,
                    " to Journal: ",
                    self.journal.issn_l,
                    self.journal.title,
                )

            # else:
            #     print("Price already in database: ", self.journal.title)
        elif not self.journal:
            print(
                "Could not add price due to missing journal:",
                self.issn,
            )
        elif not self.price:
            print(
                "Could not add price due to missing price:",
                self.issn,
            )

    def get_country_entries(self):
        return (
            db.session.query(SubscriptionPrice)
            .filter_by(
                price=self.price,
                currency_id=self.currency.id,
                region_id=None,
                country_id=self.country_id,
                fte_from=self.fte_from,
                fte_to=self.fte_to,
                year=self.year,
            )
            .all()
        )

    def get_region_entries(self):
        return (
            db.session.query(SubscriptionPrice)
            .filter_by(
                price=self.price,
                currency_id=self.currency.id,
                region_id=self.current_region.id,
                country_id=None,
                fte_from=self.fte_from,
                fte_to=self.fte_to,
                year=self.year,
            )
            .all()
        )

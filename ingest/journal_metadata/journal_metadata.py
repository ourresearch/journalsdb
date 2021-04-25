import string

import pandas as pd

from app import db
from models.journal import Journal, JournalMetadata


class JournalMetaDataImporter:

    """
    Ingestion script for Journal Metadata
    Takes a dataframe and saves all rows into the database
    """

    def __init__(self, df):
        self.df = df
        self.md = None
        self.j = None
        self.org_list = []

    def cleanse_data(self):
        """
        Removes excess rows and replaces NaN with None so
        issues do not occur with insertions
        """
        self.df = self.df.loc[:, ~self.df.columns.str.contains("^Unnamed")]
        self.df = self.df.where(pd.notnull(self.df), None)

    def ingest_metadata(self):
        """
        Iterates through the CSV and saves journal metadata into the database.
        """
        for index, row in self.df.iterrows():
            issn = row["issn"]
            if issn:
                self.j = db.session.query(Journal).filter_by(issn_l=issn).one_or_none()
                if self.j:
                    self.create_md(row)
                    self.update_society(row)
                    db.session.add(self.md)
                    db.session.commit()
                else:
                    print("Could not find Journal for ISSN: ", issn)
            self.md = None
            self.j = None
            self.org_list = []

    def create_md(self, row):
        """
        Creates a JournalMetadata db entry and adds data from spreadsheet
        to the db entry.
        """
        home_page_url = row["home_page"]
        author_instructions_url = row["author_instructions"]
        editorial_page_url = row["editorial_board"]
        facebook_url = row["facebook_url"]
        linkedin_url = row["linkedin_url"]
        twitter_url = row["twitter_url"]
        wikidata_url = row["wikidata_url"]
        accurate_title = row["accurate_title"]

        self.md = (
            db.session.query(JournalMetadata)
            .filter_by(journal_id=self.j.id)
            .one_or_none()
        )

        if not self.md:
            self.md = JournalMetadata()
            self.md.journal_id = self.j.id

        if accurate_title and not self.j.is_modified_title:
            accurate_title = string.capwords(accurate_title.lower())
            self.j.is_modified_title = True
            self.j.title = accurate_title

        self.md.home_page_url = home_page_url
        self.md.author_instructions_url = author_instructions_url
        self.md.editorial_page_url = editorial_page_url
        self.md.facebook_url = facebook_url
        self.md.linkedin_url = linkedin_url
        self.md.twitter_url = twitter_url
        self.md.wikidata_url = wikidata_url

    def update_society(self, row):
        """
        Creates a list of dictionaries to store in the journal's society journal
        information.

        Format
        [
            {
                "organization": Name,
                "url": https://url.com,
            },
        ]
        """
        society_organization_1 = row["society_organization_1"]
        society_organization_link_1 = row["society_organization_link_1"]
        self.process_society(society_organization_1, society_organization_link_1)

        society_organization_2 = row["society_organization_2"]
        society_organization_link_2 = row["society_organization_link_2"]
        self.process_society(society_organization_2, society_organization_link_2)

        society_organization_3 = row["society_organization_3"]
        society_organization_link_3 = row["society_organization_link_3"]
        self.process_society(society_organization_3, society_organization_link_3)

        if self.org_list:
            self.md.societies = self.org_list
        else:
            self.md.societies = None

    def process_society(self, organization, link):
        """
        Adds a single organization, url dictionary to the organization list
        """
        if organization:
            self.md.is_society_journal = True
            d = {
                "organization": organization,
                "url": link,
            }
            self.org_list.append(d)

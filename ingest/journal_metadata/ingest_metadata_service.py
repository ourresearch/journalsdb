import re
import string

import pandas as pd

from app import db
from models.journal import Journal, JournalMetadata


class JournalMetaDataService:
    """
    Ingestion script that reads data from a CSV and imports it into the journal_metadata table.
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.md = None
        self.journal = None
        self.org_list = []

    def read_data(self):
        """
        Read the CSV into a pandas dataframe.
        """
        self.df = pd.read_csv(self.file_path)

    def clean_data(self):
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
            issn = self.get_issn(row["issn"])
            if issn:
                self.journal = Journal.find_by_issn(issn)
                if self.journal:
                    self.create_md(row)
                    self.update_society(row)
                    db.session.add(self.md)
                    db.session.commit()
                else:
                    print("Could not find journal for ISSN {}".format(issn))
            self.md = None
            self.journal = None
            self.org_list = []

    @staticmethod
    def get_issn(issn):
        """
        Some ISSNs are formatted as a list like [""1938-9736"", ""1946-9837""].
        We can find and use the first ISSN that is found with regex.
        """
        return re.search(r"\w{4}-\w{4}", issn).group()

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
            .filter_by(journal_id=self.journal.id)
            .one_or_none()
        )

        if self.md:
            print("Updating metadata for ISSN {}".format(self.journal.issn_l))
        else:
            self.md = JournalMetadata()
            self.md.journal_id = self.journal.id
            print(
                "Creating new metadata record for ISSN {}".format(self.journal.issn_l)
            )

        if accurate_title and not self.journal.is_modified_title:
            accurate_title = string.capwords(accurate_title.lower())
            self.journal.is_modified_title = True
            self.journal.title = accurate_title

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

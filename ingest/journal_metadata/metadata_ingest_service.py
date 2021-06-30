import re
import string

import pandas as pd

from app import db
from models.journal import Journal, JournalMetadata


class JournalMetaDataIngestService:
    """
    Ingestion script that reads data from a CSV and imports it into the journal_metadata table.
    """

    def __init__(self, file_path):
        self.df = None
        self.file_path = file_path
        self.journal = None
        self.metadata = None
        self.societies = []

    def ingest_metadata(self):
        """
        Read the CSV file, clean the data, then save or update the records in the database.
        """
        self.read_data()
        self.clean_data()
        self.save_data()

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

    def save_data(self):
        """
        Iterates through the CSV and saves journal metadata into the database.
        """
        for index, row in self.df.iterrows():
            issn = self.get_issn(row["issn"])
            self.journal = Journal.find_by_issn(issn)
            self.create_or_update_metadata(row)
            self.create_or_update_societies(row)
            db.session.add(self.metadata)
            db.session.commit()

            # reset for next loop
            self.metadata = None
            self.journal = None
            self.societies = []

    @staticmethod
    def get_issn(issn):
        """
        Some ISSNs are formatted as a list like [""1938-9736"", ""1946-9837""].
        We can find and use the first ISSN that is found with regex.
        """
        return re.search(r"\w{4}-\w{4}", issn).group()

    def create_or_update_metadata(self, row):
        """
        Creates or updates a JournalMetadata entry.
        """
        self.metadata = (
            db.session.query(JournalMetadata)
            .filter_by(journal_id=self.journal.id)
            .one_or_none()
        )

        if self.metadata:
            print("Updating metadata for ISSN {}".format(self.journal.issn_l))
        else:
            self.metadata = JournalMetadata()
            self.metadata.journal_id = self.journal.id
            print(
                "Creating new metadata record for ISSN {}".format(self.journal.issn_l)
            )

        accurate_title = row["accurate_title"]
        if accurate_title and not self.journal.is_modified_title:
            accurate_title = string.capwords(accurate_title.lower())
            self.journal.is_modified_title = True
            self.journal.title = accurate_title

        self.metadata.home_page_url = row["home_page"]
        self.metadata.author_instructions_url = row["author_instructions"]
        self.metadata.editorial_page_url = row["editorial_board"]
        self.metadata.facebook_url = row["facebook_url"]
        self.metadata.linkedin_url = row["linkedin_url"]
        self.metadata.twitter_url = row["twitter_url"]
        self.metadata.wikidata_url = row["wikidata_url"]

    def create_or_update_societies(self, row):
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

        if self.societies:
            self.metadata.societies = self.societies
        else:
            self.metadata.societies = None

    def process_society(self, organization, link):
        """
        Adds a single organization, url dictionary to the organization list
        """
        if organization:
            self.metadata.is_society_journal = True
            d = {
                "organization": organization,
                "url": link,
            }
            self.societies.append(d)

import datetime
import json

import requests
from sqlalchemy import exc

from app import db
from ingest.utils import get_or_create
from ingest.journals.utils import remove_control_characters
from models.issn import (
    ISSNMetaData,
    LinkedISSNL,
)
from models.journal import Journal, Publisher


class NewJournal:
    def __init__(self, issn_metadata):
        self.issn_metadata = issn_metadata

    def process(self):
        """
        Core function that processes each issn_metadata record.
        If a journal title is found in either the issn.org or crossref API, then a new Journal is added to the database.
        If a publisher name is found in crossref, then that is added to the new journal as well.
        """
        self.save_issn_org_api()
        self.save_crossref_api()

        title = self.get_title()
        publisher = self.get_publisher()

        if title:
            self.save_journal(title, publisher)

        self.link_issn_l()
        self.mark_as_updated()

    def save_issn_org_api(self):
        issn_org_url = "https://portal.issn.org/resource/ISSN/{}?format=json".format(
            self.issn_metadata.issn_l
        )
        try:
            r = requests.get(issn_org_url)
            if r.status_code == 200 and "@graph" in r.json():
                self.issn_metadata.issn_org_raw_api = r.json()
                db.session.commit()
                print(
                    "saving issn_metadata org data for issn_metadata {}".format(
                        self.issn_metadata.issn_l
                    )
                )
            else:
                print(
                    "no issn_metadata org data found for {}".format(
                        self.issn_metadata.issn_l
                    )
                )
        except (requests.exceptions.ConnectionError, json.JSONDecodeError):
            return

    def save_crossref_api(self):
        crossref_url = "https://api.crossref.org/journals/{}".format(
            self.issn_metadata.issn_l
        )
        try:
            r = requests.get(crossref_url)
            if r.status_code == 200:
                self.issn_metadata.crossref_raw_api = r.json()
                self.issn_metadata.crossref_issns = (
                    self.issn_metadata.issns_from_crossref_api
                )
                db.session.commit()
                print(
                    "saving crossref data for issn_metadata {}".format(
                        self.issn_metadata.issn_l
                    )
                )
            else:
                print(
                    "no crossref data for issn_metadata {}".format(
                        self.issn_metadata.issn_l
                    )
                )
        except requests.exceptions.ConnectionError:
            return None

    def get_title(self):
        """
        Get a journal title from issn.org. If it does not exist, try crossref.
        """
        title = None

        if self.issn_metadata.issn_org_raw_api:
            title = self.title_from_issn_org()
        elif not title and self.issn_metadata.crossref_raw_api:
            title = self.title_from_crossref()

        if title:
            title = self.format_title(title)
        return title

    def title_from_crossref(self):
        if "title" in self.issn_metadata.crossref_raw_api["message"]:
            title = self.issn_metadata.crossref_raw_api["message"]["title"]
        else:
            title = None
        return title

    def title_from_issn_org(self):
        try:
            # find element with name or mainTitle
            title_dict = next(
                d
                for d in self.issn_metadata.issn_org_raw_api["@graph"]
                if "name" in d.keys() or "mainTitle" in d.keys()
            )
        except StopIteration:
            return None

        title = (
            title_dict["mainTitle"]
            if "mainTitle" in title_dict
            else title_dict.get("name")
        )
        if isinstance(title, list):
            # get shortest title from the list
            if "." in title:
                title.remove(".")
            title = min(title, key=len)

        return title

    @staticmethod
    def format_title(title):
        title = title.strip()
        if title and title[-1] == ".":
            title = title[:-1]
        title = remove_control_characters(title)
        return title

    def get_publisher(self):
        """
        Gets or creates a publisher object if publisher name exists in crossref.
        """
        publisher_name = self.publisher_name_from_crossref()
        if publisher_name:
            formatted_name = self.format_publisher_name(publisher_name)
            normalized_name = self.normalize_publisher_name(formatted_name)
            publisher = get_or_create(db.session, Publisher, name=normalized_name)
            return publisher

    def publisher_name_from_crossref(self):
        if self.issn_metadata.crossref_raw_api:
            publisher_name = self.issn_metadata.crossref_raw_api["message"]["publisher"]
        else:
            publisher_name = None
        return publisher_name

    @staticmethod
    def format_publisher_name(name):
        name = name.strip('"').strip()
        return name

    @staticmethod
    def normalize_publisher_name(name):
        if "informa uk" in name.lower():
            name = "Taylor & Francis"
        elif "wiley" in name.lower():
            name = "Wiley"
        elif "springer" in name.lower() and name != "Springer Publishing Company":
            name = "Springer Nature"
        elif "sage publications" in name.lower():
            name = "SAGE"
        return name

    def save_journal(self, title, publisher):
        j = Journal(issn_l=self.issn_metadata.issn_l, title=title, publisher=publisher)
        db.session.add(j)
        db.session.commit()
        print(
            "added new journal with issn_l {}, title {}, publisher {}".format(
                self.issn_metadata.issn_l, title, publisher
            )
        )

    def link_issn_l(self):
        try:
            # if the issn_l is in a different record issn_metadata, then link it
            issn_l_in_crossref_issns = ISSNMetaData.query.filter(
                ISSNMetaData.crossref_issns.contains(
                    json.dumps(self.issn_metadata.issn_l)
                )
            ).all()
            for issn_l_in_crossref in issn_l_in_crossref_issns:
                if issn_l_in_crossref.issn_l != self.issn_metadata.issn_l:
                    db.session.add(
                        LinkedISSNL(
                            issn_l_primary=self.issn_metadata.issn_l,
                            issn_l_secondary=issn_l_in_crossref.issn_l,
                            reason="crossref",
                        )
                    )
                db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
            return

    def mark_as_updated(self):
        self.issn_metadata.updated_at = datetime.datetime.now()
        db.session.commit()

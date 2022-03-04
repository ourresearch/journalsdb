import datetime

import requests
from requests.exceptions import RequestException

from app import db
from models.journal import Journal


class DateLastDOIStatus:
    def __init__(self):
        self.api_url = "https://api.crossref.org/journals/{}/works?sort=published&rows=1&mailto=team@ourresearch.org"

    def update_date_last_doi(self):
        for journal in self.page_query(db.session.query(Journal)):
            try:
                r = requests.get(self.api_url.format(journal.issn_l))
                if r.status_code == 404:
                    for issn in journal.issns:
                        if journal.issn_l != issn:
                            r = requests.get(self.api_url.format(issn))
                            if r.status_code == 200:
                                break
            except RequestException:
                # go to next record
                continue

            if r.status_code == 200 and r.json()["message"]["items"]:
                try:
                    # full date
                    published = r.json()["message"]["items"][0]["published"]
                    year = published["date-parts"][0][0]
                    month = published["date-parts"][0][1]
                    day = published["date-parts"][0][2]
                    self.set_last_doi_date(journal, year, month, day)
                except (KeyError, IndexError):
                    try:
                        # year only
                        published = r.json()["message"]["items"][0]["published"]
                        year = published["date-parts"][0][0]
                        self.set_last_doi_date(journal, year, 1, 1)
                    except (KeyError, IndexError):
                        print(
                            "issue with issn {} (index out of range).".format(
                                journal.issn_l
                            )
                        )
            db.session.commit()

    @staticmethod
    def set_last_doi_date(journal, year, month, day):
        recent_article_date = "{} {} {}".format(year, month, day)
        status_as_of = datetime.datetime.strptime(recent_article_date, "%Y %m %d")
        # handle manual input of a recent date
        # if not journal.date_last_doi or (
        #     journal.date_last_doi and status_as_of > journal.date_last_doi
        # ):
        journal.date_last_doi = status_as_of
        print(
            "setting issn {} with date last doi of {}".format(
                journal.issn_l, status_as_of
            )
        )

    @staticmethod
    def page_query(q):
        """Run query with limited memory."""
        offset = 0
        while True:
            r = False
            for elem in q.limit(1000).offset(offset):
                r = True
                yield elem
            offset += 1000
            if not r:
                break

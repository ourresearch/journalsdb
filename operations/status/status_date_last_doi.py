import datetime

import requests
from sqlalchemy.orm import lazyload

from app import db
from models.journal import Journal


class DateLastDOIStatus:
    def __init__(self):
        self.api_url = "https://api.crossref.org/journals/{}/works?sort=published&rows=1&mailto=team@ourresearch.org"

    def update_date_last_doi(self):
        journals = db.session.query(Journal).filter(Journal.date_last_doi == None).all()
        for journal in journals:
            r = requests.get(self.api_url.format(journal.issn_l))
            if r.status_code == 404:
                for issn in journal.issns:
                    if journal.issn_l != issn:
                        r = requests.get(self.api_url.format(issn))
                        if r.status_code == 200:
                            break

            if r.status_code == 200 and r.json()["message"]["items"]:
                try:
                    created = r.json()["message"]["items"][0]["created"]
                    year = created["date-parts"][0][0]
                    month = created["date-parts"][0][1]
                    day = created["date-parts"][0][2]
                    self.set_last_doi_date(journal, year, month, day)
                except IndexError:
                    print(
                        "issue with issn {} (index out of range).".format(
                            journal.issn_l
                        )
                    )
            db.session.commit()

    @staticmethod
    def journals_to_update():
        return db.session.query(Journal).order_by(Journal.status_as_of.desc()).all()

    @staticmethod
    def set_last_doi_date(journal, year, month, day):
        recent_article_date = "{} {} {}".format(year, month, day)
        status_as_of = datetime.datetime.strptime(recent_article_date, "%Y %m %d")
        # handle manual input of a recent date
        if not journal.date_last_doi or (
            journal.date_last_doi and status_as_of > journal.date_last_doi
        ):
            journal.date_last_doi = status_as_of
            print(
                "setting issn {} with date last doi of {}".format(
                    journal.issn_l, status_as_of
                )
            )

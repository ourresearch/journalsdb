import datetime

import requests

from app import db
from models.journal import Journal, JournalStatus


class CurrentlyPublishingStatus:
    def __init__(self):
        self.api_url = "https://api.crossref.org/journals/{}/works?filter=from-created-date:{}&sort=published&rows=1&mailto=team@ourresearch.org"

    def update_status(self):
        journals = self.journals_to_update()
        for journal in journals:
            six_months_ago = self.six_months_ago()
            r = requests.get(self.api_url.format(journal.issn_l, six_months_ago))

            if r.status_code == 200:
                if r.json()["message"]["items"]:
                    try:
                        created = r.json()["message"]["items"][0]["created"]
                        year = created["date-parts"][0][0]
                        month = created["date-parts"][0][1]
                        day = created["date-parts"][0][2]
                        self.update_as_publishing(journal, year, month, day)
                    except IndexError:
                        print(
                            "issue with issn {} (index out of range).".format(
                                journal.issn_l
                            )
                        )
                else:
                    self.update_as_unknown(journal)
            else:
                self.update_as_unknown(journal)

    @staticmethod
    def six_months_ago():
        return datetime.datetime.strftime(
            datetime.datetime.now() - datetime.timedelta(6 * 30), "%Y-%m-%d"
        )  # now minus six months in format 2021-01-01

    @staticmethod
    def journals_to_update():
        return (
            db.session.query(Journal)
            .filter(Journal.status == "unknown")
            .order_by(Journal.status_as_of.desc())
            .limit(1000)
            .all()
        )

    @staticmethod
    def update_as_publishing(journal, year, month, day):
        recent_article_date = "{} {} {}".format(year, month, day)
        if (
            journal.status.value == JournalStatus.UNKNOWN.value
            or journal.status.value == JournalStatus.PUBLISHING.value
        ):
            journal.status = JournalStatus.PUBLISHING.value
            journal.status_as_of = datetime.datetime.strptime(
                recent_article_date, "%Y %m %d"
            )
            print(
                "setting issn {} as currently publishing with year {} and month {}".format(
                    journal.issn_l, year, month
                )
            )
            db.session.commit()

    @staticmethod
    def update_as_unknown(journal):
        journal.status_as_of = datetime.datetime.now()
        print("keeping issn {} as unknown with current date".format(journal.issn_l))
        db.session.commit()

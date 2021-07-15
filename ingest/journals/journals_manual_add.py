import datetime

from app import db
from models.issn import ISSNToISSNL, ISSNMetaData
from models.journal import Journal


class ManualAdd:
    def __init__(self, issn, journal_title, publisher_id):
        self.issn = issn
        self.journal_title = journal_title
        self.publisher_id = publisher_id

    def add_journal(self):
        self.add_issn_to_issnl_mapping()
        self.add_issn_to_issn_org_issns()
        self.save_journal_record()

    def add_issn_to_issnl_mapping(self):
        issn_to_issnl = ISSNToISSNL(issn_l=self.issn, issn=self.issn)
        db.session.add(issn_to_issnl)
        db.session.commit()
        print(
            "issn {} mapped to {} in issn to issnl table".format(self.issn, self.issn)
        )

    def add_issn_to_issn_org_issns(self):
        metadata = ISSNMetaData(
            issn_l=self.issn,
            issn_org_issns=[self.issn],
            updated_at=datetime.datetime.now(),
        )
        db.session.add(metadata)
        db.session.commit()
        print(
            "issn {} added to issn_org column for {} issn_l metadata record".format(
                self.issn, self.issn
            )
        )

    def save_journal_record(self):
        j = Journal(
            issn_l=self.issn,
            title=self.journal_title,
            publisher_id=int(self.publisher_id),
        )
        db.session.add(j)
        db.session.commit()
        print(
            "journal saved {} {} {}".format(
                self.issn, self.journal_title, int(self.publisher_id)
            )
        )

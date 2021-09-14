from app import db
from models.issn import ISSNMetaData, ISSNToISSNL
from models.journal import Journal
from models.usage import DOICount, OpenAccess


class MergeIssn:
    def __init__(self, issn_from, issn_to):
        self.issn_from = issn_from
        self.issn_to = issn_to
        self.old_issns = []
        self.old_title = None

    def merge_issn(self):
        self.delete_old_journal()
        self.delete_old_issn_metadata()
        self.delete_old_issn_to_issnl()
        self.delete_old_doi_data()
        self.delete_old_open_access_data()
        self.map_issns_to_new_issn_l()
        self.add_issn_to_new_issn_org_issns()
        self.set_other_title()

    def delete_old_journal(self):
        j = db.session.query(Journal).filter_by(issn_l=self.issn_from).one()
        if j.subscription_prices or j.apc_prices:
            raise Exception(
                "subscription or apc price exists for journal to be deleted."
            )

        self.old_title = j.title
        db.session.delete(j)
        db.session.commit()
        print("journal entry for issn {} deleted".format(self.issn_from))

    def delete_old_issn_metadata(self):
        i = db.session.query(ISSNMetaData).filter_by(issn_l=self.issn_from).one()
        self.old_issns = i.issn_org_issns
        db.session.delete(i)
        db.session.commit()
        print("issn metadata for issn {} deleted".format(self.issn_from))

    def delete_old_issn_to_issnl(self):
        issns_to_remove = (
            db.session.query(ISSNToISSNL).filter_by(issn_l=self.issn_from).all()
        )
        for issn in issns_to_remove:
            db.session.delete(issn)
            db.session.commit()
            print(
                "issn to issnl mapping data for issn {} and issn_l {} deleted".format(
                    issn.issn, issn.issn_l
                )
            )

    def delete_old_doi_data(self):
        dois = db.session.query(DOICount).filter_by(issn_l=self.issn_from).one_or_none()
        if dois:
            db.session.delete(dois)
            db.session.commit()

    def delete_old_open_access_data(self):
        open_access = (
            db.session.query(OpenAccess).filter_by(issn_l=self.issn_from).all()
        )
        for o in open_access:
            db.session.delete(o)
        db.session.commit()

    def map_issns_to_new_issn_l(self):
        for old_issn in self.old_issns:
            issn_to_issnl = ISSNToISSNL(issn_l=self.issn_to, issn=old_issn)
            db.session.add(issn_to_issnl)
            db.session.commit()
            print(
                "issn {} mapped to {} in issn to issnl table".format(
                    self.issn_from, self.issn_to
                )
            )

    def add_issn_to_new_issn_org_issns(self):
        metadata = db.session.query(ISSNMetaData).filter_by(issn_l=self.issn_to).one()
        metadata.issn_org_issns = metadata.issn_org_issns + self.old_issns
        metadata.previous_issn_ls = (
            metadata.previous_issn_ls + [self.issn_from]
            if metadata.previous_issn_ls
            else [self.issn_from]
        )
        db.session.commit()
        print(
            "issn {} added to issn_org column for {} issn_l metadata record".format(
                self.issn_from, self.issn_to
            )
        )

    def set_other_title(self):
        j = db.session.query(Journal).filter_by(issn_l=self.issn_to).one()
        if j.title.lower() != self.old_title.lower():
            j.other_titles = (
                j.other_titles + [self.old_title]
                if j.other_titles
                else [self.old_title]
            )
        db.session.commit()
        print(
            "set other title {} on journal with title {}".format(
                self.old_title, j.title
            )
        )

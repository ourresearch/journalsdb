from app import db
from models.issn import ISSNMetaData, ISSNToISSNL
from models.journal import Journal


class MoveIssn:
    def __init__(self, issn_from, issn_to):
        self.issn_from = issn_from
        self.issn_to = issn_to

    def move_issn(self):
        self.delete_old_journal()
        self.delete_old_issn_metadata()
        self.delete_old_issn_to_issnl()
        self.map_issn_to_new_issn_l()
        self.add_issn_to__new_issn_org_issns()

    def delete_old_journal(self):
        j = db.session.query(Journal).filter_by(issn_l=self.issn_from).one_or_none()
        if j:
            db.session.delete(j)
            db.session.commit()
            print("journal entry for issn {} deleted".format(self.issn_from))
        else:
            # journal may have been mapped to different issn_l
            r = db.session.query(ISSNToISSNL).filter_by(issn=self.issn_from).first()
            if r and r.issn_l != self.issn_to:
                issn_l = r.issn_l
                j = db.session.query(Journal).filter_by(issn_l=issn_l).one()
                db.session.delete(j)
                db.session.commit()
                print("journal entry deleted using mapped issn_l {}".format(issn_l))

    def delete_old_issn_metadata(self):
        i = (
            db.session.query(ISSNMetaData)
            .filter_by(issn_l=self.issn_from)
            .one_or_none()
        )
        if i:
            db.session.delete(i)
            db.session.commit()
            print("issn metadata for issn {} deleted".format(self.issn_from))
        else:
            # metadata may have been mapped to different issn_l
            r = db.session.query(ISSNToISSNL).filter_by(issn=self.issn_from).first()
            if r and r.issn_l != self.issn_to:
                issn_l = r.issn_l
                i = db.session.query(ISSNMetaData).filter_by(issn_l=issn_l).one()
                db.session.delete(i)
                db.session.commit()
                print("issn metadata deleted using mapped issn_l {}".format(issn_l))

    def delete_old_issn_to_issnl(self):
        issn_to_remove = (
            db.session.query(ISSNToISSNL).filter_by(issn=self.issn_from).first()
        )
        if issn_to_remove:
            mapped_issns = (
                db.session.query(ISSNToISSNL)
                .filter_by(issn_l=issn_to_remove.issn_l)
                .all()
            )
            for issn in mapped_issns:
                db.session.delete(issn)
                db.session.commit()
                print(
                    "issn to issnl mapping data for issn {} and issn_l {} deleted".format(
                        issn.issn, issn.issn_l
                    )
                )

    def map_issn_to_new_issn_l(self):
        issn_to_issnl = ISSNToISSNL(issn_l=self.issn_to, issn=self.issn_from)
        db.session.add(issn_to_issnl)
        db.session.commit()
        print(
            "issn {} mapped to {} in issn to issnl table".format(
                self.issn_from, self.issn_to
            )
        )

    def add_issn_to__new_issn_org_issns(self):
        metadata = db.session.query(ISSNMetaData).filter_by(issn_l=self.issn_to).one()
        metadata.issn_org_issns = metadata.issn_org_issns + [self.issn_from]
        db.session.commit()
        print(
            "issn {} added to issn_org column for {} issn_l metadata record".format(
                self.issn_from, self.issn_to
            )
        )

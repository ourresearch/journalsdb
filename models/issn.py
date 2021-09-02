import datetime

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app import db


class ISSNTemp(db.Model):
    __tablename__ = "issn_temp"

    issn = db.Column(db.String(9), nullable=False, primary_key=True, unique=True)
    issn_l = db.Column(db.String(9), nullable=False, primary_key=True, index=True)
    has_crossref = db.Column(db.Boolean, default=False)


class ISSNToISSNL(db.Model):
    __tablename__ = "issn_to_issnl"

    issn = db.Column(
        db.String(9), nullable=False, primary_key=True, index=True, unique=True
    )
    issn_l = db.Column(db.String(9), nullable=False, primary_key=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ISSNHistory(db.Model):
    __tablename__ = "issn_history"

    id = db.Column(db.Integer, primary_key=True)
    issn_l = db.Column(db.String(9), nullable=False)
    issn = db.Column(db.String(9), nullable=False)
    status = db.Column(db.String, nullable=False)
    occurred_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ISSNMetaData(db.Model):
    __tablename__ = "issn_metadata"

    issn_l = db.Column(db.String, primary_key=True)
    issn_org_issns = db.Column(JSONB)
    crossref_issns = db.Column(JSONB)
    previous_issn_ls = db.Column(JSONB)
    issn_org_raw_api = db.Column(JSONB)
    crossref_raw_api = db.Column(JSONB)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    __table_args__ = (
        db.Index("idx_crossref_issns", crossref_issns, postgresql_using="gin"),
        db.Index("idx_issn_org_issns", issn_org_issns, postgresql_using="gin"),
        db.Index(
            "issn_metadata__index_updated_at_nulls",
            updated_at,
            updated_at.desc(),
        ),
    )

    @property
    def issns_from_crossref_api(self):
        return (
            self.crossref_raw_api["message"]["ISSN"] if self.crossref_raw_api else None
        )

    @property
    def issns(self):
        return self.issn_org_issns


class LinkedISSNL(db.Model):
    __tablename__ = "linked_issn_l"

    issn_l_primary = db.Column(db.ForeignKey("issn_metadata.issn_l"), primary_key=True)
    issn_l_secondary = db.Column(
        db.ForeignKey("issn_metadata.issn_l"), primary_key=True
    )
    reason = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())


class MissingJournal(db.Model):
    __tablename__ = "missing_journals"

    id = db.Column(db.Integer, primary_key=True)
    issn = db.Column(db.String(9))
    status = db.Column(db.String(100))
    processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

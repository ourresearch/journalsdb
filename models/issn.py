import datetime
import json

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app import db


class ISSNTemp(db.Model):
    __tablename__ = "issn_temp"

    issn = db.Column(db.String(9), nullable=False, primary_key=True)
    issn_l = db.Column(db.String(9), nullable=False, primary_key=True, index=True)


class ISSNToISSNL(db.Model):
    __tablename__ = "issn_to_issnl"

    issn = db.Column(db.String(9), nullable=False, primary_key=True)
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
    issn_org_raw_api = db.Column(JSONB)
    crossref_raw_api = db.Column(JSONB)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    __table_args__ = (
        db.Index("idx_crossref_issns", crossref_issns, postgresql_using="gin"),
        db.Index("idx_issn_org_issns", issn_org_issns, postgresql_using="gin"),
    )

    @property
    def title_from_issn_api(self):
        title_dict = next(
            d
            for d in self.issn_org_raw_api["@graph"]
            if "name" in d.keys() or "mainTitle" in d.keys()
        )
        title = (
            title_dict["mainTitle"]
            if "mainTitle" in title_dict
            else title_dict.get("name")
        )
        title = title[0] if isinstance(title, list) else title
        return title

    @property
    def issns_from_crossref_api(self):
        return (
            self.crossref_raw_api["message"]["ISSN"] if self.crossref_raw_api else None
        )


class LinkedISSNL(db.Model):
    issn_l_primary = db.Column(db.ForeignKey("issn_metadata.issn_l"), primary_key=True)
    issn_l_secondary = db.Column(
        db.ForeignKey("issn_metadata.issn_l"), primary_key=True
    )
    reason = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

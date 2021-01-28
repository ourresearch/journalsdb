import datetime

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app import db


class ISSNTemp(db.Model):
    __tablename__ = "issn_temp"
    issn_l = db.Column(db.String(9), nullable=False, primary_key=True)
    issn = db.Column(db.String(9), nullable=False, primary_key=True)


class ISSNToISSNL(db.Model):
    __tablename__ = "issn_to_issnl"

    issn_l = db.Column(db.String(9), nullable=False, primary_key=True)
    issn = db.Column(db.String(9), nullable=False, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ISSNMetaData(db.Model):
    __tablename__ = "issn_metadata"

    id = db.Column(db.Integer, primary_key=True)
    issn_l = db.Column(db.String, nullable=False, unique=True)
    issn_org_issns = db.Column(JSONB)
    crossref_issns = db.Column(JSONB)
    issn_org_raw_api = db.Column(JSONB)
    crossref_raw_api = db.Column(JSONB)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

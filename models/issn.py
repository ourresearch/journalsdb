import datetime

from app import db


class ISSNToISSNL(db.Model):
    __tablename__ = "issn_to_issnl"

    issn_l = db.Column(db.String(9), nullable=False, primary_key=True)
    issn = db.Column(db.String(9), nullable=False, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
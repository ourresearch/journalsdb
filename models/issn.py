from sqlalchemy.dialects.postgresql import JSONB

from app import db
from models.mixins import TimestampMixin


class RawISSNOrgData(db.Model, TimestampMixin):
    __tablename__ = "raw_issn_org_data"

    id = db.Column(db.Integer, primary_key=True)
    issn_l = db.Column(db.String(9), unique=True, nullable=False)
    issns = db.Column(JSONB)

import datetime

from app import db
from models.mixins import TimestampMixin


class OpenAccess(db.Model, TimestampMixin):
    __tablename__ = "open_access"

    id = db.Column(db.Integer, primary_key=True)
    issn_l = db.Column(db.Text, nullable=False, index=True)
    title = db.Column(db.Text)
    year = db.Column(db.Integer, nullable=False)
    num_dois = db.Column(db.Integer)
    num_open = db.Column(db.Integer)
    open_rate = db.Column(db.Float)
    num_green = db.Column(db.Integer)
    green_rate = db.Column(db.Float)
    num_bronze = db.Column(db.Integer)
    bronze_rate = db.Column(db.Float)
    num_hybrid = db.Column(db.Integer)
    hybrid_rate = db.Column(db.Float)
    num_gold = db.Column(db.Integer)
    gold_rate = db.Column(db.Float)
    is_in_doaj = db.Column(db.Boolean)
    is_gold_journal = db.Column(db.Boolean)

    __table_args__ = (db.UniqueConstraint("issn_l", "year"),)

    @classmethod
    def recent_status(cls, journal_id):
        return (
            cls.query.filter_by(journal_id=journal_id).order_by(cls.year.desc()).first()
        )

    def to_dict(self):
        return {
            "year": self.year,
            "is_in_doaj": self.is_in_doaj,
            "is_gold_journal": self.is_gold_journal,
        }


class Repository(db.Model, TimestampMixin):
    __tablename__ = "repositories"

    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(
        db.Integer, db.ForeignKey("journals.id"), nullable=False, index=True
    )
    journal = db.relationship("Journal", backref=db.backref("repositories", lazy=True))
    endpoint_id = db.Column(db.Text, nullable=False)
    repository_name = db.Column(db.Text)
    institution_name = db.Column(db.Text)
    home_page = db.Column(db.Text)
    pmh_url = db.Column(db.Text)
    num_articles = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "endpoint_id": self.endpoint_id,
            "repository_name": self.repository_name,
            "institution_name": self.institution_name,
            "home_page": self.home_page,
            "pmh_url": self.pmh_url,
            "num_articles": self.num_articles,
        }


class ExtensionRequests(db.Model, TimestampMixin):
    __tablename__ = "extension_requests"

    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(
        db.Integer, db.ForeignKey("journals.id"), nullable=False, index=True
    )
    journal = db.relationship(
        "Journal", backref=db.backref("extension_requests", lazy=True)
    )
    month = db.Column(db.DateTime, nullable=False)
    requests = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "month": datetime.datetime.strftime(self.month, "%B"),
            "year": datetime.datetime.strftime(self.month, "%Y"),
            "requests": self.requests,
        }

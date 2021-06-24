import datetime

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UniqueConstraint

from app import db
from models.journal import Journal
from models.mixins import TimestampMixin


class DOICount(db.Model, TimestampMixin):
    __tablename__ = "doi_counts"

    issn_l = db.Column(db.String(9), primary_key=True)
    dois_by_year = db.Column(JSONB, nullable=False)
    sample_dois = db.Column(JSONB)

    @property
    def total_dois(self):
        return sum(self.dois_by_year.values())

    @property
    def dois_by_year_sorted(self):
        dois = {int(k): v for (k, v) in self.dois_by_year.items()}
        return list(sorted(dois.items(), reverse=True))

    @property
    def sample_doi_urls(self):
        return (
            ["https://doi.org/{}".format(doi) for doi in self.sample_dois]
            if self.sample_dois
            else None
        )


class ExtensionRequests(db.Model, TimestampMixin):
    __tablename__ = "extension_requests"

    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(
        db.Integer,
        db.ForeignKey("journals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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


class OpenAccess(db.Model, TimestampMixin):
    __tablename__ = "open_access"

    issn_l = db.Column(db.Text, primary_key=True, nullable=False, index=True)
    title = db.Column(db.Text)
    year = db.Column(db.Integer, primary_key=True, nullable=False)
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

    def to_dict(self):
        dict_ = {}
        for key in self.__mapper__.c.keys():
            dict_[key] = getattr(self, key)

        fields_to_remove = ["issn_l", "title", "created_at", "updated_at"]
        for field in fields_to_remove:
            dict_.pop(field)

        # sort by key
        dict_ = dict(sorted(dict_.items()))

        return dict_


class Repository(db.Model):
    __tablename__ = "repositories"

    issn_l = db.Column(db.Text, primary_key=True, index=True)
    endpoint_id = db.Column(db.Text, primary_key=True, nullable=False)
    repository_name = db.Column(db.Text)
    institution_name = db.Column(db.Text)
    home_page = db.Column(db.Text)
    pmh_url = db.Column(db.Text)
    num_articles = db.Column(db.Integer, nullable=False)
    __table_args__ = (UniqueConstraint("issn_l", "endpoint_id", name="uix_1"),)

    @classmethod
    def repositories(cls, issn_l):
        return cls.query.filter_by(issn_l=issn_l).all()

    def to_dict(self):
        return {
            "endpoint_id": self.endpoint_id,
            "repository_name": self.repository_name,
            "institution_name": self.institution_name,
            "home_page": self.home_page,
            "pmh_url": self.pmh_url,
            "num_articles": self.num_articles,
        }


class RetractionWatch(db.Model):
    __tablename__ = "retraction_watch"

    record_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    journal = db.Column(db.Text, nullable=False)
    publisher = db.Column(db.Text, nullable=False)
    retraction_date = db.Column(db.DateTime, nullable=False)
    retraction_doi = db.Column(db.String(100), nullable=False)
    paper_doi = db.Column(db.String(100), nullable=False)
    published_year = db.Column(db.Integer)
    issn = db.Column(db.String(9))


class RetractionSummary(db.Model):
    __tablename__ = "retraction_summary"

    id = db.Column(db.Integer, primary_key=True)
    issn = db.Column(db.String(9))
    journal = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    retractions = db.Column(db.Integer, nullable=False)
    num_dois = db.Column(db.Integer)
    __table_args__ = (db.UniqueConstraint("issn", "year"),)

    @classmethod
    def retractions_by_year(cls, issn_l):
        retractions_by_year = []

        retractions = cls.retractions_by_issn(issn_l)

        if retractions:
            for r in retractions:
                percent_retracted = (r.retractions / r.num_dois) * 100
                retractions_by_year.append(
                    {
                        "year": r.year,
                        "retractions": r.retractions,
                        "percent_retracted": float("{:.3}".format(percent_retracted)),
                    }
                )

        # provenance
        if len(retractions_by_year) > 0:
            return {
                "provenance": "https://retractionwatch.com/",
                "retractions_by_year": retractions_by_year,
            }
        else:
            return None

    @classmethod
    def retractions_by_issn(cls, issn_l):
        """
        Go through all available journal ISSNs to try and match it to retractions.
        """
        # try issn_l
        retractions = cls.query.filter_by(issn=issn_l).all()
        if retractions:
            return retractions

        # try other associated issns
        journal = Journal.find_by_issn(issn_l)
        if journal:
            for issn in journal.issns:
                retractions = cls.query.filter_by(issn=issn).all()
                if retractions:
                    return retractions
            return None

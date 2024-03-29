from datetime import datetime
import enum
import json

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import shortuuid

from app import db
from models.issn import ISSNMetaData
from models.mixins import TimestampMixin
from models.subjects import journal_subjects
from models.usage import DOICount


class JournalStatus(enum.Enum):
    """
    Choices for journal status field. Must run a migration after changing.
    """

    CEASED = "ceased"
    INCORPORATED = "incorporated"
    PUBLISHING = "publishing"
    RENAMED = "renamed"
    UNKNOWN = "unknown"


class Journal(db.Model):
    __tablename__ = "journals"

    id = db.Column(db.Integer, primary_key=True)
    issn_l = db.Column(
        db.String(9), db.ForeignKey("issn_metadata.issn_l"), unique=True, nullable=False
    )
    title = db.Column(db.Text, nullable=False)
    other_titles = db.Column(JSONB)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id"), index=True)
    internal_publisher_id = db.Column(db.Text)
    imprint_id = db.Column(db.Integer, db.ForeignKey("imprints.id"))
    status = db.Column(
        db.Enum(JournalStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default="unknown",
    )
    status_as_of = db.Column(db.DateTime, nullable=True)
    date_last_doi = db.Column(db.DateTime, nullable=True)
    uuid = db.Column(db.Text, default=shortuuid.uuid, unique=True)
    is_modified_title = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, server_default=func.now(), nullable=False, index=True
    )
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # relationships
    apc_metadata = db.relationship(
        "APCMetadata", uselist=False, lazy=True, backref="journal"
    )
    apc_prices = db.relationship(
        "APCPrice",
        lazy="subquery",
        backref="journal",
        order_by="[desc(APCPrice.year), APCPrice.price]",
    )
    author_permissions = db.relationship("AuthorPermissions", cascade="all, delete")
    citations = db.relationship(
        "Citation", back_populates="journal", uselist=False, cascade="all, delete"
    )
    doi_counts = db.relationship(
        "DOICount",
        primaryjoin="Journal.issn_l == foreign(DOICount.issn_l)",
        uselist=False,
        viewonly=True,
    )
    imprint = db.relationship("Imprint")
    issn_metadata = db.relationship("ISSNMetaData")
    journal_metadata = db.relationship(
        "JournalMetadata", backref="journal", cascade="all, delete"
    )
    open_access = db.relationship(
        "OpenAccess",
        primaryjoin="Journal.issn_l == foreign(OpenAccess.issn_l)",
        order_by="desc(OpenAccess.year)",
        viewonly=True,
    )
    permissions = db.relationship("AuthorPermissions", uselist=False, backref="journal")
    publisher = db.relationship(
        "Publisher", backref=db.backref("journals", lazy=True), lazy="joined"
    )
    subjects = db.relationship("Subject", secondary=journal_subjects)
    subscription_prices = db.relationship(
        "SubscriptionPrice",
        lazy="subquery",
        backref="journal",
        order_by="[desc(SubscriptionPrice.year), SubscriptionPrice.price]",
    )

    @classmethod
    def find_by_issn(cls, issn):
        # try to find by issn_l
        journal = cls.query.filter_by(issn_l=issn).one_or_none()
        if journal:
            return journal

        # find in issn_org issns
        metadata_record = ISSNMetaData.query.filter(
            ISSNMetaData.issn_org_issns.contains(json.dumps(issn))
        ).first()

        if metadata_record:
            return cls.query.filter_by(issn_l=metadata_record.issn_l).one_or_none()

    @classmethod
    def find_by_synonym(cls, synonym):
        return cls.query.filter(
            cls.other_titles.contains(json.dumps(synonym))
        ).one_or_none()

    @property
    def issns(self):
        return self.issn_metadata.issns

    @property
    def open_access_recent(self):
        return self.open_access[0] if self.open_access else None

    @property
    def total_dois(self):
        """Returns doi total for current and previous issn_ls combined."""
        total = self.doi_counts.total_dois if self.doi_counts else None
        if self.issn_metadata and self.issn_metadata.previous_issn_ls:
            for issn in self.issn_metadata.previous_issn_ls:
                doi_counts = DOICount.query.filter_by(issn_l=issn).one_or_none()
                if doi_counts:
                    if total:
                        total = total + doi_counts.total_dois
                    else:
                        total = doi_counts.total_dois
        return total

    @property
    def dois_by_year(self):
        """Returns sorted dois by year for current and former journals combined."""
        dois_by_year = {}

        if self.doi_counts:
            # add current journal dois by year
            dois_by_year.update(
                {int(k): v for (k, v) in self.doi_counts.dois_by_year.items()}
            )

        if self.issn_metadata and self.issn_metadata.previous_issn_ls:
            for issn in self.issn_metadata.previous_issn_ls:
                doi_counts = DOICount.query.filter_by(issn_l=issn).one_or_none()
                if doi_counts:
                    # add former journal dois by year
                    dois_by_year.update(
                        {int(k): v for (k, v) in doi_counts.dois_by_year.items()}
                    )
        dois_combined_and_sorted = list(sorted(dois_by_year.items(), reverse=True))
        return dois_combined_and_sorted

    @property
    def apc_source(self):
        if self.apc_metadata and self.apc_metadata.apc_source:
            return self.apc_metadata.apc_source
        elif self.publisher:
            return self.publisher.apc_data_source


class JournalMetadata(db.Model, TimestampMixin):
    __tablename__ = "journal_metadata"

    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(
        db.Integer, db.ForeignKey("journals.id"), nullable=False, index=True
    )
    home_page_url = db.Column(db.String(500))
    author_instructions_url = db.Column(db.String(500))
    editorial_page_url = db.Column(db.String(500))
    facebook_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))
    twitter_url = db.Column(db.String(500))
    wikidata_url = db.Column(db.String(500))
    is_society_journal = db.Column(db.Boolean, default=False)
    societies = db.Column(JSONB)


class Publisher(db.Model, TimestampMixin):
    __tablename__ = "publishers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    publisher_synonyms = db.Column(JSONB)
    uuid = db.Column(db.Text, default=shortuuid.uuid, unique=True)
    sub_data_source = db.Column(db.String(500), nullable=True, index=False)
    apc_data_source = db.Column(db.String(500), nullable=True, index=False)

    def __repr__(self):
        return self.name


class Imprint(db.Model, TimestampMixin):
    __tablename__ = "imprints"

    id = db.Column(db.Integer, primary_key=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id"), nullable=False)
    name = db.Column(db.Text, unique=True, nullable=False)

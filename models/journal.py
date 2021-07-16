from collections import OrderedDict
from datetime import datetime
import enum
import json

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import shortuuid

from app import db
from models.issn import ISSNMetaData
from models.mixins import TimestampMixin
from models.price import journal_subscription_price, journal_apc_price
from models.subjects import journal_subjects


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
    journal_synonyms = db.Column(JSONB)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id"), index=True)
    internal_publisher_id = db.Column(db.Text)
    imprint_id = db.Column(db.Integer, db.ForeignKey("imprints.id"))
    status = db.Column(
        db.Enum(JournalStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default="unknown",
    )
    status_as_of = db.Column(db.DateTime, nullable=True)
    uuid = db.Column(db.Text, default=shortuuid.uuid, unique=True)
    is_modified_title = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, server_default=func.now(), nullable=False, index=True
    )
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # relationships
    apc_prices = db.relationship(
        "APCPrice", secondary=journal_apc_price, lazy="subquery", backref="journals"
    )
    author_permissions = db.relationship("AuthorPermissions", cascade="all, delete")
    doi_counts = db.relationship(
        "DOICount",
        primaryjoin="Journal.issn_l == foreign(DOICount.issn_l)",
        uselist=False,
    )
    imprint = db.relationship("Imprint", cascade="all, delete")
    issn_metadata = db.relationship("ISSNMetaData")
    journal_metadata = db.relationship(
        "JournalMetadata", backref="journal", cascade="all, delete"
    )
    open_access = db.relationship(
        "OpenAccess",
        primaryjoin="Journal.issn_l == foreign(OpenAccess.issn_l)",
        order_by="desc(OpenAccess.year)",
    )
    permissions = db.relationship("AuthorPermissions", uselist=False, backref="journal")
    publisher = db.relationship(
        "Publisher", backref=db.backref("journals", lazy=True), lazy="joined"
    )
    subjects = db.relationship("Subject", secondary=journal_subjects)
    subscription_prices = db.relationship(
        "SubscriptionPrice",
        secondary=journal_subscription_price,
        lazy="subquery",
        backref="journals",
    )

    @classmethod
    def find_by_issn(cls, issn):
        # try to find by issn_l
        journal = cls.query.filter_by(issn_l=issn).one_or_none()
        if journal:
            return journal

        # find in issn_org issns
        issn_in_issn_org = ISSNMetaData.query.filter(
            ISSNMetaData.issn_org_issns.contains(json.dumps(issn))
        ).first()

        # find in crossref issns
        issn_in_crossref = ISSNMetaData.query.filter(
            ISSNMetaData.crossref_issns.contains(json.dumps(issn))
        ).first()

        metadata_record = issn_in_issn_org or issn_in_crossref
        if metadata_record:
            return cls.query.filter_by(issn_l=metadata_record.issn_l).one_or_none()

    @classmethod
    def find_by_synonym(cls, synonym):
        return cls.query.filter(
            cls.synonyms.contains(json.dumps(synonym))
        ).one_or_none()

    @property
    def issns(self):
        return self.issn_metadata.issns

    @property
    def current_journal(self):
        """Returns a single current_journal that is pulled from the JournalRenamed table if it exists."""
        return (
            self.current_journals[0].current_journal if self.current_journals else None
        )

    def to_dict(self):
        return OrderedDict(
            {
                "issn_l": self.issn_l,
                "issns": self.issns,
                "title": self.title,
                "publisher": self.publisher.name if self.publisher else "",
            }
        )


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

    def to_dict(self):
        dict_ = {}
        for key in self.__mapper__.c.keys():
            dict_[key] = getattr(self, key)

        fields_to_remove = ["id", "journal_id", "created_at", "updated_at"]
        for field in fields_to_remove:
            dict_.pop(field)

        return dict_


class JournalRenamed(db.Model):
    """
    This model maps old journals that have been renamed (former_issn_l) to their current version (current_issn_l).
    """

    __tablename__ = "journals_renamed"

    current_issn_l = db.Column(
        db.String(9), db.ForeignKey("journals.issn_l"), primary_key=True, index=True
    )
    former_issn_l = db.Column(
        db.String(9), db.ForeignKey("journals.issn_l"), primary_key=True, unique=True
    )
    created_at = db.Column(db.DateTime, server_default=func.now())
    current_journal = db.relationship(
        "Journal", foreign_keys=[current_issn_l], backref="journals_renamed"
    )
    former_journal = db.relationship(
        "Journal", foreign_keys=[former_issn_l], backref="current_journals"
    )


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

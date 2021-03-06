import json

from sqlalchemy.dialects.postgresql import JSONB
import shortuuid

from app import db
from models.issn import ISSNMetaData
from models.mixins import TimestampMixin
from models.price import journal_subscription_price, journal_apc_price
from models.subjects import journal_subjects


class Journal(db.Model, TimestampMixin):
    __tablename__ = "journals"

    id = db.Column(db.Integer, primary_key=True)
    issn_l = db.Column(
        db.String(9), db.ForeignKey("issn_metadata.issn_l"), unique=True, nullable=False
    )
    title = db.Column(db.Text, nullable=False)
    synonyms = db.Column(JSONB)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id"), index=True)
    internal_publisher_id = db.Column(db.Text)
    imprint_id = db.Column(db.Integer, db.ForeignKey("imprints.id"))
    discount_waiver_exception = db.Column(db.Boolean, default=False, nullable=False)
    uuid = db.Column(db.Text, default=shortuuid.uuid, unique=True)

    # relationships
    apc_prices = db.relationship(
        "APCPrice", secondary=journal_apc_price, lazy="subquery"
    )
    author_permissions = db.relationship("AuthorPermissions")
    imprint = db.relationship("Imprint")
    issn_metadata = db.relationship("ISSNMetaData")
    journal_metadata = db.relationship(
        "JournalMetadata", lazy="joined", backref="journal"
    )
    permissions = db.relationship("AuthorPermissions", uselist=False, backref="journal")
    publisher = db.relationship("Publisher", backref=db.backref("journals", lazy=True))
    subjects = db.relationship("Subject", secondary=journal_subjects, lazy="subquery")
    subscription_prices = db.relationship(
        "SubscriptionPrice", secondary=journal_subscription_price, lazy="subquery"
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

    def to_dict(self):
        return {
            "issn_l": self.issn_l,
            "issns": self.issns,
            "title": self.title,
            "publisher": self.publisher.name if self.publisher else "",
        }


class JournalMetadata(db.Model, TimestampMixin):
    __tablename__ = "journal_metadata"

    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(db.Integer, db.ForeignKey("journals.id"), nullable=False)
    author_page_url = db.Column(db.Text)
    editorial_page_url = db.Column(db.Text)
    twitter_id = db.Column(db.Text)
    wikidata_id = db.Column(db.Text)
    society_journal = db.Column(db.Boolean)
    society_journal_name = db.Column(db.Text)


class Publisher(db.Model, TimestampMixin):
    __tablename__ = "publishers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    synonyms = db.Column(JSONB)
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

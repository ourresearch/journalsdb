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
        if not self.issn_org_raw_api:
            return self.title_from_crossref_api
        else:
            try:
                # find element with name or mainTitle
                title_dict = next(
                    d
                    for d in self.issn_org_raw_api["@graph"]
                    if "name" in d.keys() or "mainTitle" in d.keys()
                )
            except StopIteration:
                return self.title_from_crossref_api

        title = (
            title_dict["mainTitle"]
            if "mainTitle" in title_dict
            else title_dict.get("name")
        )
        if isinstance(title, list):
            # get shortest title from the list
            if "." in title:
                title.remove(".")
            title = min(title, key=len)
        title = title.strip()
        return title

    @property
    def title_from_crossref_api(self):
        if not self.crossref_raw_api:
            return
        else:
            if "title" in self.crossref_raw_api["message"]:
                return self.crossref_raw_api["message"]["title"]

    @property
    def issns_from_crossref_api(self):
        return (
            self.crossref_raw_api["message"]["ISSN"] if self.crossref_raw_api else None
        )

    @property
    def publisher(self):
        name = (
            self.crossref_raw_api["message"]["publisher"]
            if self.crossref_raw_api
            else None
        )
        name = name.strip('"').strip() if name else None

        # normalize publisher
        if name and "informa uk" in name.lower():
            name = "Taylor & Francis"
        elif name and "wiley" in name.lower():
            name = "Wiley"
        elif (
            name
            and "springer" in name.lower()
            and name != "Springer Publishing Company"
        ):
            name = "Springer Nature"
        elif name and "sage publications" in name.lower():
            name = "SAGE"

        return name

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

    issn = db.Column(db.String(9), primary_key=True)
    processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

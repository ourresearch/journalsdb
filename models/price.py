from sqlalchemy import func

from app import db
from models.location import Country, Region
from models.mixins import TimestampMixin


class SubscriptionPrice(db.Model, TimestampMixin):
    __tablename__ = "subscription_price"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency_id = db.Column(
        db.Integer, db.ForeignKey("currency.id"), nullable=False, index=True
    )
    country_id = db.Column(db.Integer, db.ForeignKey("countries.id"), index=True)
    region_id = db.Column(db.Integer, db.ForeignKey("regions.id"), index=True)
    fte_from = db.Column(db.Integer)
    fte_to = db.Column(db.Integer)
    year = db.Column(db.Integer, nullable=False, index=True)

    # relationships
    country = db.relationship("Country", lazy="joined")
    currency = db.relationship("Currency", lazy="joined")
    region = db.relationship("Region", lazy="joined")

    def to_dict(self):
        return {
            "fte_from": self.fte_from,
            "fte_to": self.fte_to,
            "price": str(self.price),
            "currency": self.currency.acronym,
            "region": self.region.name if self.region else None,
            "country": self.country.name if self.country else None,
            "year": self.year,
        }


class APCPrice(db.Model):
    __tablename__ = "apc_price"

    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(
        db.Integer, db.ForeignKey("journals.id"), nullable=False, index=True
    )
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency_id = db.Column(
        db.Integer, db.ForeignKey("currency.id"), nullable=False, index=True
    )
    country_id = db.Column(db.Integer, db.ForeignKey("countries.id"))
    region_id = db.Column(db.Integer, db.ForeignKey("regions.id"))
    year = db.Column(db.Integer, nullable=False, index=True)
    apc_waived = db.Column(db.Boolean, default=False, nullable=False)
    discounted = db.Column(db.Boolean, default=False, nullable=False)
    discount_reason = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, server_default=func.now())

    # relationships
    country = db.relationship("Country", lazy="joined")
    currency = db.relationship("Currency", lazy="joined")
    region = db.relationship("Region", lazy="joined")


class APCMetadata(db.Model, TimestampMixin):
    __tablename__ = "apc_metadata"

    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(
        db.Integer, db.ForeignKey("journals.id"), nullable=False, index=True
    )
    apc_source = db.Column(db.String(128))
    apc_required = db.Column(db.Boolean, default=True, nullable=False)
    apc_funded_by = db.Column(db.String(128))
    notes = db.Column(db.Text)

    # relationship
    journal = db.relationship("Journal", uselist=False, backref="apc_metadata")


class Currency(db.Model):
    __tablename__ = "currency"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(3), unique=False, nullable=False)
    text = db.Column(db.String(128), unique=True, nullable=False)
    acronym = db.Column(db.String(3), unique=True, nullable=False)


journal_mini_bundle_price = db.Table(
    "journal_mini_bundle_price",
    db.Column(
        "mini_bundle_id", db.Integer, db.ForeignKey("mini_bundles.id"), primary_key=True
    ),
    db.Column(
        "subscription_price_id",
        db.Integer,
        db.ForeignKey("subscription_price.id"),
        primary_key=True,
    ),
)

mini_bundle_journals = db.Table(
    "mini_bundle_journals",
    db.Column(
        "mini_bundle_id", db.Integer, db.ForeignKey("mini_bundles.id"), primary_key=True
    ),
    db.Column("journal_id", db.Integer, db.ForeignKey("journals.id"), primary_key=True),
)


class MiniBundle(db.Model, TimestampMixin):
    __tablename__ = "mini_bundles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    issn = db.Column(db.Text)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id"))
    publisher = db.relationship(
        "Publisher", backref=db.backref("mini_bundles", lazy=True)
    )

    journals = db.relationship(
        "Journal",
        secondary=mini_bundle_journals,
        lazy="subquery",
        backref="mini_bundles",
        order_by="Journal.title",
    )

    subscription_prices = db.relationship(
        "SubscriptionPrice",
        secondary=journal_mini_bundle_price,
        lazy="subquery",
        backref="mini_bundles",
        order_by="[desc(SubscriptionPrice.year), SubscriptionPrice.price]",
    )

    def to_dict(self):
        return {
            "mini_bundle_name": self.name,
            "journals_included": [
                {"issn_l": j.issn_l, "title": j.title} for j in self.journals
            ],
            "prices": sorted(
                [p.to_dict() for p in self.subscription_prices],
                key=lambda p: p["year"],
                reverse=True,
            ),
        }


journal_subscription_price = db.Table(
    "journal_subscription_price",
    db.Column("journal_id", db.Integer, db.ForeignKey("journals.id"), primary_key=True),
    db.Column(
        "subscription_price_id",
        db.Integer,
        db.ForeignKey("subscription_price.id"),
        primary_key=True,
    ),
)

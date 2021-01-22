from app import db
from models.location import Country, Region
from models.mini_bundle import MiniBundle
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


class APCPrice(db.Model, TimestampMixin):
    __tablename__ = "apc_price"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency_id = db.Column(
        db.Integer, db.ForeignKey("currency.id"), nullable=False, index=True
    )
    country_id = db.Column(db.Integer, db.ForeignKey("countries.id"), index=True)
    region_id = db.Column(db.Integer, db.ForeignKey("regions.id"), index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    notes = db.Column(db.Text)


class Currency(db.Model):
    __tablename__ = "currency"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(3), unique=True, nullable=False)


# many to many tables
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

journal_apc_price = db.Table(
    "journal_apc_price",
    db.Column("journal_id", db.Integer, db.ForeignKey("journals.id"), primary_key=True),
    db.Column(
        "apc_price_id", db.Integer, db.ForeignKey("apc_price.id"), primary_key=True
    ),
)

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

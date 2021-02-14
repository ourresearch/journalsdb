from app import db
from models.mixins import TimestampMixin


class Region(db.Model, TimestampMixin):
    __tablename__ = "regions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=False, nullable=False)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id"))
    publisher = db.relationship("Publisher", backref=db.backref("regions", lazy=True))


class Country(db.Model, TimestampMixin):
    __tablename__ = "countries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    iso = db.Column(db.String(2), unique=True, nullable=False)
    iso3 = db.Column(db.String(3), unique=True, nullable=False)
    continent_id = db.Column(db.Integer, db.ForeignKey("continents.id"), index=True)
    continent = db.relationship("Continent", backref=db.backref("countries", lazy=True))


class Continent(db.Model, TimestampMixin):
    __tablename__ = "continents"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)


# many to many table
region_countries = db.Table(
    "region_countries",
    db.Column("region_id", db.Integer, db.ForeignKey("regions.id"), primary_key=True),
    db.Column(
        "country_id", db.Integer, db.ForeignKey("countries.id"), primary_key=True
    ),
)

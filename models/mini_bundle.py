from app import db
from models.mixins import TimestampMixin


class MiniBundle(db.Model, TimestampMixin):
    __tablename__ = "mini_bundles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    issn = db.Column(db.Text)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id"))
    publisher = db.relationship(
        "Publisher", backref=db.backref("mini_bundles", lazy=True)
    )


# many to many table
mini_bundle_journals = db.Table(
    "mini_bundle_journals",
    db.Column(
        "mini_bundle_id", db.Integer, db.ForeignKey("mini_bundles.id"), primary_key=True
    ),
    db.Column("journal_id", db.Integer, db.ForeignKey("journals.id"), primary_key=True),
)

from app import db
from models.mixins import TimestampMixin


class Subject(db.Model, TimestampMixin):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)


# many to many table
journal_subjects = db.Table(
    "journal_subjects",
    db.Column("journal_id", db.Integer, db.ForeignKey("journals.id"), primary_key=True),
    db.Column("subject_id", db.Integer, db.ForeignKey("subjects.id"), primary_key=True),
)

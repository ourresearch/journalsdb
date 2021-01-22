from datetime import datetime

from sqlalchemy.ext.declarative import declared_attr

from app import db


class TimestampMixin(object):
    """
    Adds created_at and updated_at fields to any model.
    Written as a @declared_attr so the fields are placed at the end of a table.
    """

    @declared_attr
    def created_at(cls):
        return db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @declared_attr
    def updated_at(cls):
        return db.Column(db.DateTime, onupdate=datetime.utcnow)

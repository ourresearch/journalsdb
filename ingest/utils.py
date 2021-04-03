import unicodedata
import urllib.request

import pandas as pd
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql

from app import db
from models.journal import Journal


class CSVImporter:
    def __init__(self, fields, table, url, primary_keys=None):
        self.fields = fields
        self.table = table
        self.url = url
        self.primary_keys = primary_keys
        self.chunksize = 10000  # Update based on memory constraints
        self.base = declarative_base()
        self.metadata = MetaData(db.engine, reflect=True)

    def import_data(self):
        """
        Very fast way to copy 1 million or more rows into a table.
        """
        chunks = pd.read_csv(
            self.get_file(),
            compression="gzip",
            sep=",",
            quotechar='"',
            error_bad_lines=False,
            chunksize=self.chunksize,
        )
        for chunk in chunks:
            chunk = self.organize_chunk(chunk)
            self.upsert(chunk)

    def organize_chunk(self, chunk):
        """
        Overridden in inherited objects.
        """
        pass

    def upsert(self, chunk):
        """
        Performs a Postgresql Upsert.

        Will update all columns based on the provided primary keys.
        """
        table = self.metadata.tables.get(self.table)
        update_cols = [c.name for c in table.c if c not in self.primary_keys]
        stmt = postgresql.insert(table).values(chunk)

        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=self.primary_keys,
            set_={k: getattr(stmt.excluded, k) for k in update_cols},
        )
        db.session.execute(on_conflict_stmt)
        db.session.commit()

    def get_file(self):
        """
        Opens remote file.
        """
        response = urllib.request.urlopen(self.url)
        return response


def find_journal(issn):
    """
    Find journal by ISSN.
    """
    return Journal.find_by_issn(issn)


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def remove_control_characters(s):
    """
    Remove control characters such as SOS and ST from a string.
    Exists in many issn.org journal title.
    """
    if s:
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

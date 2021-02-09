import csv
import gzip
import unicodedata
import urllib.request

from app import db
from models.journal import Journal


class CSVImporter:
    def __init__(self, table_name, url):
        self.table_name = table_name
        self.staging_table = table_name + '_staging'
        self.url = url

    def import_data(self):
        self.create_temp_table()
        self.copy_csv_to_temp_table()

    def get_file(self):
        """
        Opens remote file.
        """
        response = urllib.request.urlopen(self.url)
        gzip_file = gzip.GzipFile(fileobj=response)
        return gzip_file

    def copy_csv_to_temp_table(self):
        """
        Very fast way to copy 1 million or more rows into a table.
        """
        copy_sql = "COPY {} FROM STDOUT WITH (FORMAT CSV, DELIMITER ',', HEADER, ENCODING 'ISO_8859_5')".format(self.staging_table)
        conn = db.engine.raw_connection()
        with conn.cursor() as cur:
            cur.copy_expert(copy_sql, self.get_file())
        conn.commit()

    def create_temp_table(self):
        db.session.execute('CREATE TABLE {} ( like {} including all)'.format(self.staging_table, self.table_name))
        db.session.commit()

    def drop_temp_table(self):
        db.session.execute('DROP TABLE IF EXISTS {}'.format(self.staging_table))
        db.session.commit()


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

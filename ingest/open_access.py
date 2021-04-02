import pandas as pd

from app import app
from ingest.utils import CSVImporter
from models.usage import OpenAccess


@app.cli.command("import_open_access")
def import_open_access():
    """
    Open access data: https://api.unpaywall.org/journal_open_access.csv.gz

    Counts the number of articles with each oa_status by (issn_l, year).
    num_open = num_green + num_bronze + num_hybrid + num_gold
    {status}_rate = num_{status} / num_dois

    issn_l (string, pkey)
    title (string, nullable)
    year (integer, pkey)
    num_dois (integer)
    num_open (integer)
    open_rate (double precision)
    num_green (integer)
    green_rate (double precision)
    num_bronze (integer)
    bronze_rate (double precision)
    num_hybrid (integer)
    hybrid_rate (double precision)
    num_gold (integer)
    gold_rate (double precision)
    is_in_doaj (boolean)
    is_gold_journal (boolean)

    Run with: flask import_open_access
    """

    class OpenAccessImporter(CSVImporter):
        def organize_chunk(self, chunk):
            """
            Chunks may contain null values which should be replaced with None.
            SQLalchemy doesn't keep column names in order, so the chunk must be fitted to
            SQLalchemy's default order
            """
            chunk = chunk.where(pd.notnull(chunk), None)
            chunk = chunk.dropna(axis=0, subset=["issn_l", "year"])
            chunk = chunk[
                [
                    "issn_l",
                    "title",
                    "year",
                    "num_dois",
                    "num_open",
                    "open_rate",
                    "num_green",
                    "green_rate",
                    "num_bronze",
                    "bronze_rate",
                    "num_hybrid",
                    "hybrid_rate",
                    "num_gold",
                    "gold_rate",
                    "is_in_doaj",
                    "is_gold_journal",
                ]
            ]
            return chunk.values.tolist()

    url = "https://api.unpaywall.org/journal_open_access.csv.gz"

    # field setup
    fields = OpenAccess.__table__.columns.keys()
    fields_to_remove = ["created_at", "updated_at"]
    for field in fields_to_remove:
        fields.remove(field)
    fields = ",".join(fields)
    primary_keys = ["issn_l", "year"]
    importer = OpenAccessImporter(
        fields=fields,
        table="open_access",
        url=url,
        primary_keys=primary_keys,
    )
    importer.import_data()

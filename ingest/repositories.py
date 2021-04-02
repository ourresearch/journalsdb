import pandas as pd

from app import app
from ingest.utils import CSVImporter
from models.usage import Repository


@app.cli.command("import_repositories")
def import_repositories():
    """
    Repository article counts: https://api.unpaywall.org/repositories.csv.gz

    issn_l (string, pkey)
    endpoint_id (string, pkey)
    repository_name  (string, nullable)
    institution_name (string, nullable)
    home_page (string, nullable)
    pmh_url (string, nullable)
    num_articles (integer)

    Run with: flask import_repositories
    """

    class RepositoryImporter(CSVImporter):
        def organize_chunk(self, chunk):
            """
            Chunks may contain null values which should be replaced with None.
            SQLalchemy doesn't keep column names in order, so the chunk must be fitted to
            SQLalchemy's default order
            """
            chunk = chunk.where(pd.notnull(chunk), None)
            chunk = chunk[
                [
                    "issn_l",
                    "endpoint_id",
                    "repository_name",
                    "institution_name",
                    "home_page",
                    "pmh_url",
                    "num_articles",
                ]
            ]
            return chunk.values.tolist()

    fields = Repository.__table__.columns.keys()
    fields = ",".join(fields)
    primary_keys = ["issn_l", "endpoint_id"]
    importer = RepositoryImporter(
        fields=fields,
        table="repositories",
        url="https://api.unpaywall.org/repositories.csv.gz",
        primary_keys=primary_keys,
    )
    importer.import_data()

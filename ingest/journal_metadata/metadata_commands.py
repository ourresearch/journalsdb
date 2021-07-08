import os

import click

from app import app
from ingest.journal_metadata.metadata_service import JournalMetaDataIngestService

CSV_DIRECTORY = "ingest/journal_metadata/files/"


@app.cli.command("ingest_metadata")
@click.option("--file_name", required=True)
def ingest_metadata(file_name):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    md_service = JournalMetaDataIngestService(file_path)
    md_service.ingest_metadata()

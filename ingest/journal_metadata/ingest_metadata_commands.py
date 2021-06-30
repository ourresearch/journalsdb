import os

import click
import pandas as pd

from app import app
from ingest.journal_metadata.ingest_metadata_service import JournalMetaDataService
from ingest.journal_metadata.ingest_metadata_service_elsevier import (
    cleanse_data,
    ElsevierMetaDataService,
)

CSV_DIRECTORY = "ingest/journal_metadata/files/"


@app.cli.command("import_md")
@click.option("--file_name", required=True)
def import_md(file_name):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    j = JournalMetaDataService(file_path)
    j.read_data()
    j.clean_data()
    j.ingest_metadata()


@app.cli.command("import_elsevier_md")
@click.option("--file_name", default="Elsevier.csv", required=True)
def import_elsevier_md(file_name):
    """
    Old way to ingest metadata for Elsevier.
    """
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    df = pd.read_csv(file_path)
    df = cleanse_data(df)
    j = ElsevierMetaDataService(df)
    j.ingest_metadata()

import click
import pandas as pd

from app import app, db
from ingest.journal_metadata.elsevier_md import cleanse_data, ingest_journal_metadata


@app.cli.command("import_elsevier_md")
@click.option("--file_name", default="ingest/journal_metadata/Elsevier.csv")
def import_elsevier_md(file_name):
    df = pd.read_csv(file_name)
    df = cleanse_data(df)
    ingest_journal_metadata(df)

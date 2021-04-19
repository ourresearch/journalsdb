import click
import pandas as pd

from app import app, db
from ingest.journal_metadata.journal_metadata import JournalMetaDataImporter
from ingest.journal_metadata.elsevier_md import cleanse_data, ElsevierMD
from ingest.journal_metadata.wiley_md import cleanse_wiley_data
from ingest.journal_metadata.sage_md import cleanse_sage_data


@app.cli.command("import_elsevier_md")
@click.option("--file_name", default="ingest/journal_metadata/Elsevier.csv")
def import_elsevier_md(file_name):
    df = pd.read_csv(file_name)
    df = cleanse_data(df)
    j = ElsevierMD(df)
    j.ingest_metadata()


@app.cli.command("import_wiley_md")
@click.option("--file_name", default="ingest/journal_metadata/Wiley.csv")
def import_wiley_md(file_name):
    df = pd.read_csv(file_name)
    df = cleanse_wiley_data(df)
    j = JournalMetaDataImporter(df)
    j.ingest_metadata()


@app.cli.command("import_sage_md")
@click.option("--file_name", default="ingest/journal_metadata/Sage.csv")
def import_sage_md(file_name):
    df = pd.read_csv(file_name)
    df = cleanse_sage_data(df)
    j = JournalMetaDataImporter(df)
    j.ingest_metadata()

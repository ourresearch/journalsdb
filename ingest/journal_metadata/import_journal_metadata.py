import click
import pandas as pd

from app import app, db
from ingest.journal_metadata.journal_metadata import JournalMetaDataImporter
from ingest.journal_metadata.elsevier_md import cleanse_data, ElsevierMD


@app.cli.command("import_tf_md")
@click.option("--file_name", default="ingest/journal_metadata/taylor_francis.csv")
def import_tf_md(file_name):
    df = pd.read_csv(file_name)
    j = JournalMetaDataImporter(df)
    j.cleanse_data()
    j.ingest_metadata()


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
    j = JournalMetaDataImporter(df)
    j.cleanse_data()
    j.ingest_metadata()


@app.cli.command("import_sage_md")
@click.option("--file_name", default="ingest/journal_metadata/Sage.csv")
def import_sage_md(file_name):
    df = pd.read_csv(file_name)
    j = JournalMetaDataImporter(df)
    j.cleanse_data()
    j.ingest_metadata()


@app.cli.command("import_springer_md")
@click.option("--file_name", default="ingest/journal_metadata/Springer.csv")
def import_springer_md(file_name):
    df = pd.read_csv(file_name)
    j = JournalMetaDataImporter(df)
    j.cleanse_data()
    j.ingest_metadata()

import click

from app import app
from ingest.journals.new_journal import NewJournal
from ingest.journals.journals_manual_add import ManualAdd
from models.issn import ISSNMetaData


@app.cli.command("process_new_journals")
def process_new_journals():
    """
    Command that iterates through issn_metadata and saves new journals if a title exists.
    """
    issns = ISSNMetaData.query.filter_by(updated_at=None).all()
    for issn_metadata in issns:
        new_journal = NewJournal(issn_metadata)
        new_journal.process()


@app.cli.command("manual_add")
@click.option("--issn", prompt=True)
@click.option("--journal_title", prompt=True)
@click.option("--publisher_id", prompt=True)
def manual_add(issn, journal_title, publisher_id):
    """
    Command used to manually add journals that are found in worldcat or somewhere else.
    """
    m = ManualAdd(issn, journal_title, publisher_id)
    m.add_journal()

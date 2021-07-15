import click

from app import app
from ingest.journals.journals_manual_add import ManualAdd


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

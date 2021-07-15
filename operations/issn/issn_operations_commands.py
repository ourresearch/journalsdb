import click

from app import app
from operations.issn.issn_move_issn import MoveIssn


@app.cli.command("move_issn")
@click.option("--issn_from", prompt=True)
@click.option("--issn_to", prompt=True)
def move_issn(issn_from, issn_to):
    """
    Transfers an ISSN mapping from one journal to another. Deletes old journal entry.
    """
    m = MoveIssn(issn_from, issn_to)
    m.move_issn()

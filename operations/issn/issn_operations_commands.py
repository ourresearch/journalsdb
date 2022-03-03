import click

from app import app
from operations.issn.issn_merge_issn import MergeIssn
from operations.issn.issn_add_cancelled_issns import add_cancelled_issns
from operations.issn.issn_move_issn import MoveIssn
from operations.issn.issn_validate_issns import validate_issns


@app.cli.command("merge_issn")
@click.option("--issn_from", prompt=True)
@click.option("--issn_to", prompt=True)
def merge_issn(issn_from, issn_to):
    """
    Merges issns together using new previous_issn_l method.
    """
    m = MergeIssn(issn_from, issn_to)
    m.merge_issn()


@app.cli.command("move_issn")
@click.option("--issn_from", prompt=True)
@click.option("--issn_to", prompt=True)
def move_issn(issn_from, issn_to):
    """
    Transfers an ISSN mapping from one journal to another. Deletes old journal entry.
    """
    m = MoveIssn(issn_from, issn_to)
    m.move_issn()


@app.cli.command("validate_issns")
@click.option("--publisher_id", prompt=True)
def validate_issns_command(publisher_id):
    """
    Validates ISSNs for a given publisher.
    """
    validate_issns(publisher_id)


@app.cli.command("add_cancelled_issns")
def add_cancelled_issns_command():
    add_cancelled_issns()

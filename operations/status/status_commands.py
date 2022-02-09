import os

import click

from app import app
from operations.status.status_from_spreadsheet import StatusFromSpreadsheet
from operations.status.status_currently_publishing import CurrentlyPublishingStatus
from operations.status.status_date_last_doi import DateLastDOIStatus

CSV_DIRECTORY = "operations/status/files/"


@app.cli.command("set_status_from_spreadsheet")
@click.option("--file_name", required=True)
def set_status_from_spreadsheet(file_name):
    """
    Iterates through a spreadsheet and sets a journal's status as discontinued, renamed, or incorporated.
    """
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    s = StatusFromSpreadsheet(file_path)
    s.update_status()


@app.cli.command("currently_publishing")
def currently_publishing():
    """
    Calls crossref API and checks recent articles to determine if a journal is currently publishing.
    """
    c = CurrentlyPublishingStatus()
    c.update_status()


@app.cli.command("date_last_doi")
def date_last_doi():
    """
    Calls crossref API and sets the date the last DOI was seen..
    """
    d = DateLastDOIStatus()
    d.update_date_last_doi()

import os

import click

from app import app
from operations.status.status_setter import StatusSetter

CSV_DIRECTORY = "operations/status/files/"


@app.cli.command("set_status")
@click.option("--file_name", required=True)
def set_status(file_name):
    """
    Iterates through a spreadsheet and sets a journal's status as discontinued, renamed, or incorporated.
    """
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    s = StatusSetter(file_path)
    s.set_journal_status()

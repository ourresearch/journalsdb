import os

from app import app
from ingest.issn import import_issns, import_issn_apis
from tests.test_client import client
from models.journal import Journal

SAMPLE_DIRECTORY = "tests/ingest/sample_data"


def test_saved_title(client):
    runner = app.test_cli_runner()

    # run initial issn-to-issn-l file
    file_path = os.path.join(
        app.root_path, SAMPLE_DIRECTORY, "ISSN-to-ISSN-L-title.txt"
    )
    runner.invoke(import_issns, ["--file_path", file_path])

    runner.invoke(import_issn_apis)

    j = Journal.query.filter_by(issn_l="0000-0027").one()
    assert j.title == "Library journal."


def test_remove_control_characters(client):
    runner = app.test_cli_runner()

    # run initial issn-to-issn-l file
    file_path = os.path.join(
        app.root_path, SAMPLE_DIRECTORY, "ISSN-to-ISSN-L-title.txt"
    )
    runner.invoke(import_issns, ["--file_path", file_path])

    runner.invoke(import_issn_apis)

    j = Journal.query.filter_by(issn_l="2119-8306").one()
    assert j.title == "Les Centralités économiques."

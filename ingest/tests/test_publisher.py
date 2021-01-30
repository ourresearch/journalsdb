import os

from app import app, db
from ingest.issn import import_issns, import_issn_apis
from ingest.tests.test_client import client
from models.journal import Journal

SAMPLE_DIRECTORY = "ingest/tests/sample_data"


def test_saved_publisher(client):
    runner = app.test_cli_runner()

    # run initial issn-to-issn-l file
    file_path = os.path.join(
        app.root_path, SAMPLE_DIRECTORY, "ISSN-to-ISSN-L-linked.txt"
    )
    runner.invoke(import_issns, ["--file_path", file_path])

    runner.invoke(import_issn_apis)

    j = Journal.query.filter_by(issn_l="2582-2810").one()
    assert j.publisher.name == "Shanlax International Journals"

    j = Journal.query.filter_by(issn_l="0974-4061").one()
    assert j.publisher.name == "Informa UK (Taylor & Francis)"

    # no publisher
    j = Journal.query.filter_by(issn_l="0000-0043").one()
    assert j.publisher is None

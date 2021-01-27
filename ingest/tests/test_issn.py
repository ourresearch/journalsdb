import os

from app import app
from ingest.issn import import_issns
from ingest.tests.test_client import client


def test_issn_import(client):
    runner = app.test_cli_runner()

    # run command
    file_path = os.path.join(app.root_path, 'ingest/tests/sample_data', 'ISSN-to-ISSN-L.txt')
    runner.invoke(import_issns, ['--file_path', file_path])
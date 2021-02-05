import os

import pytest

from app import db
from ingest.issn import import_issn_apis, import_issns
from views import app


SAMPLE_DIRECTORY = "tests/ingest/sample_data"


@pytest.fixture
def client():
    """
    Primary client that sets up the database for each test.
    """
    import requests_cache
    requests_cache.install_cache("test_cache")
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/journalsdb_test"
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            yield client
            # cleanup
            db.session.remove()
            db.drop_all()


@pytest.fixture
def run_import_issns():
    """
    This runs the command: 'flask import_issns' with a variable file name from the sample_data directory.
    """
    def _import(file_name):
        runner = app.test_cli_runner()

        # run command
        file_path = os.path.join(
            app.root_path, SAMPLE_DIRECTORY, file_name
        )
        runner.invoke(import_issns, ["--file_path", file_path])
    return _import


@pytest.fixture
def run_import_issns_with_api():
    """
    This runs the command: 'flask import_issns' with a file name followed by 'flask import_issn_apis'
    """
    def _import(file_name):
        runner = app.test_cli_runner()

        # run command
        file_path = os.path.join(
            app.root_path, SAMPLE_DIRECTORY, file_name
        )
        runner.invoke(import_issns, ["--file_path", file_path])

        # run api import
        runner.invoke(import_issn_apis)
    return _import

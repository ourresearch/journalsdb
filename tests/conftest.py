import os

import pytest

from app import db
from tests.factories import import_api_test_data
from ingest.journals.journals_commands import process_new_journals
from ingest.issn.issn_import_issns import import_issns
from views import app

NUMBER_OF_JOURNALS = 4
SAMPLE_DIRECTORY = "tests/ingest_sample_data"
TEST_DATABASE_URI = "postgresql://localhost/journalsdb_test"


@pytest.fixture(scope="module")
def api_client():
    """
    Returns a client with sample API data in the database.
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DATABASE_URI
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            import_api_test_data()
            yield client
            # cleanup
            db.session.remove()
            db.drop_all()


@pytest.fixture
def ingest_client():
    """
    Primary client that sets up the database for each ingest test.
    """
    import requests_cache

    requests_cache.install_cache("test_cache")
    app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DATABASE_URI
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
        file_path = os.path.join(app.root_path, SAMPLE_DIRECTORY, file_name)
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
        file_path = os.path.join(app.root_path, SAMPLE_DIRECTORY, file_name)
        runner.invoke(import_issns, ["--file_path", file_path])

        # run api import
        runner.invoke(process_new_journals)

    return _import

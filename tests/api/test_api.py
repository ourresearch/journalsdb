import os
import pytest

from app import db
from ingest.issn import import_issns, import_issn_apis
from tests.test_client import client
from views import app

SAMPLE_DIRECTORY = "tests/ingest/sample_data"


def test_api_root(client):
    rv = client.get("/")
    msg = rv.get_json()["msg"]
    assert rv.status_code == 200
    assert msg == "Don't panic"


def test_find_issn(client):
    # setup
    runner = app.test_cli_runner()
    file_path = os.path.join(app.root_path, SAMPLE_DIRECTORY, "ISSN-to-ISSN-L-api.txt")
    runner.invoke(import_issns, ["--file_path", file_path])
    runner.invoke(import_issn_apis)

    rv = client.get("/journal/2291-5222")
    json_data = rv.get_json()
    assert rv.status_code == 200
    assert json_data["issn_l"] == "2291-5222"
    assert json_data["issns"] == ["2291-5222"]
    assert json_data["title"] == "JMIR mhealth and uhealth."
    assert json_data["publisher"] == "JMIR Publications Inc."

    rv = client.get("/journal/0000-0043")
    json_data = rv.get_json()
    assert rv.status_code == 200
    assert json_data["issn_l"] == "0000-0043"
    assert json_data["issns"] == ["0000-0043"]
    assert json_data["title"] == "Irregular serials & annuals."
    assert json_data["publisher"] == ""

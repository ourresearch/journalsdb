import os
import time

from sqlalchemy import desc

from app import app, db
from ingest.issn import import_issns
from ingest.tests.test_client import client
from models.issn import ISSNToISSNL


def test_issn_to_issnl_import(client):
    runner = app.test_cli_runner()

    # run command
    file_path = os.path.join(app.root_path, 'ingest/tests/sample_data', 'ISSN-to-ISSN-L-initial.txt')
    runner.invoke(import_issns, ['--file_path', file_path])

    # 5 records imported
    assert ISSNToISSNL.query.count() == 5

    # check for issn_pair
    issn_pair = ISSNToISSNL.query.filter_by(issn_l='0000-0019').first()
    assert issn_pair.issn == '0000-0019'


def test_issn_new_record_added(client):
    runner = app.test_cli_runner()
    # run day one
    file_path = os.path.join(app.root_path, 'ingest/tests/sample_data', 'ISSN-to-ISSN-L-initial.txt')
    runner.invoke(import_issns, ['--file_path', file_path])

    # run day two with added record
    file_path = os.path.join(app.root_path, 'ingest/tests/sample_data', 'ISSN-to-ISSN-L-new-record.txt')
    runner.invoke(import_issns, ['--file_path', file_path])

    # sort by created_at to see new is added
    issn = ISSNToISSNL.query.order_by(desc(ISSNToISSNL.created_at)).first()
    assert issn.issn_l == '0000-0213'

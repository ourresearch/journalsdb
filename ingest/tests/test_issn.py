import os

from sqlalchemy import desc

from app import app, db
from ingest.issn import import_issns, import_issn_mappings
from ingest.tests.test_client import client
from models.issn import ISSNToISSNL, ISSNHistory


def test_issn_to_issnl_import(client):
    runner = app.test_cli_runner()

    # run command
    file_path = os.path.join(
        app.root_path, "ingest/tests/sample_data", "ISSN-to-ISSN-L-initial.txt"
    )
    runner.invoke(import_issns, ["--file_path", file_path])

    # 5 records imported
    assert ISSNToISSNL.query.count() == 5

    # check for issn_pair
    issn_pair = ISSNToISSNL.query.filter_by(issn_l="0000-0019").first()
    assert issn_pair.issn == "0000-0019"


def test_issn_import_no_changes(client):
    runner = app.test_cli_runner()

    # run command
    file_path = os.path.join(
        app.root_path, "ingest/tests/sample_data", "ISSN-to-ISSN-L-initial.txt"
    )
    runner.invoke(import_issns, ["--file_path", file_path])

    # 5 records imported
    assert ISSNToISSNL.query.count() == 5

    # run command again
    runner.invoke(import_issns, ["--file_path", file_path])

    # number of records is the same
    assert ISSNToISSNL.query.count() == 5


def test_issn_new_record_added(client):
    runner = app.test_cli_runner()
    # run day one
    file_path = os.path.join(
        app.root_path, "ingest/tests/sample_data", "ISSN-to-ISSN-L-initial.txt"
    )
    runner.invoke(import_issns, ["--file_path", file_path])

    # run day two with added record
    file_path = os.path.join(
        app.root_path, "ingest/tests/sample_data", "ISSN-to-ISSN-L-new-record.txt"
    )
    runner.invoke(import_issns, ["--file_path", file_path])

    assert ISSNToISSNL.query.count() == 6

    # sort by created_at to see new is added
    issn = ISSNToISSNL.query.order_by(desc(ISSNToISSNL.created_at)).first()
    assert issn.issn_l == "0000-0213"

    # record added to history
    h = ISSNHistory.query.filter_by(issn_l='0000-0213', issn='0000-0213').one_or_none()
    assert h is not None
    assert h.status == 'added'


def test_issn_record_removed(client):
    runner = app.test_cli_runner()
    # run day one
    file_path = os.path.join(
        app.root_path, "ingest/tests/sample_data", "ISSN-to-ISSN-L-initial.txt"
    )
    runner.invoke(import_issns, ["--file_path", file_path])

    # run day two with (0000-006X, 0000-006X) removed
    file_path = os.path.join(
        app.root_path, "ingest/tests/sample_data", "ISSN-to-ISSN-L-removed.txt"
    )
    runner.invoke(import_issns, ["--file_path", file_path])

    assert ISSNToISSNL.query.count() == 4

    # try to find removed record
    issn = ISSNToISSNL.query.filter_by(issn_l="0000-006X").first()
    assert issn is None

    # record added to history
    h = ISSNHistory.query.filter_by(issn_l='0000-006X', issn='0000-006X', status='removed').one_or_none()
    assert h is not None


# def test_issn_mappings(client):
#     runner = app.test_cli_runner()
#
#     # run initial issn-to-issn-l file
#     file_path = os.path.join(app.root_path, 'ingest/tests/sample_data', 'ISSN-to-ISSN-L-initial.txt')
#     runner.invoke(import_issns, ['--file_path', file_path])
#
#     # run mapping
#     runner.invoke(import_issn_mappings)
#
#     # test import count after group by
#     assert ISSNMetaData.query.count() == 4
#
#     # test single mapping
#     issn_l = ISSNMetaData.query.filter_by(issn_l='0000-0043').one()
#     assert issn_l.issn_org_issns == ['0000-0043']
#
#     # test mapping with two issns
#     issn_l = ISSNMetaData.query.filter_by(issn_l='0000-0019').one()
#     assert issn_l.issn_org_issns == ['0000-0019', '0000-0051']
#
#     # test created_at
#     assert issn_l.created_at is not None
#
#
# def test_issn_mapping_change(client):
#     runner = app.test_cli_runner()
#
#     # run initial issn-to-issn-l file
#     file_path = os.path.join(app.root_path, 'ingest/tests/sample_data', 'ISSN-to-ISSN-L-initial.txt')
#     runner.invoke(import_issns, ['--file_path', file_path])
#
#     # run mapping
#     runner.invoke(import_issn_mappings)
#
#     # run file with changed issns
#     file_path = os.path.join(app.root_path, 'ingest/tests/sample_data', 'ISSN-to-ISSN-L-changed.txt')
#     runner.invoke(import_issns, ['--file_path', file_path])
#
#     # run mapping
#     runner.invoke(import_issn_mappings)
#
#     # test that issn_l has the new data
#     issn_l = ISSNMetaData.query.filter_by(issn_l='0000-006X').one()
#     assert issn_l.issn_org_issns == ['0000-006X', '0000-0507']
#
#     # test updated_at is filled in
#     assert issn_l.updated_at is not None
#
#     # test that other field does not have updated_at field filled
#     second_issn_l = ISSNMetaData.query.filter_by(issn_l='0000-0043').one()
#     assert second_issn_l.updated_at is None

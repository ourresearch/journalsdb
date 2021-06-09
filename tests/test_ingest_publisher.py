import pytest

from models.journal import Journal


@pytest.mark.skip(reason="need to refactor issn import changes")
def test_saved_publisher(ingest_client, run_import_issns_with_api):
    run_import_issns_with_api("ISSN-to-ISSN-L-linked.txt")

    j = Journal.query.filter_by(issn_l="2582-2810").one()
    assert j.publisher.name == "Shanlax International Journals"

    j = Journal.query.filter_by(issn_l="0974-4061").one()
    assert j.publisher.name == "Informa UK (Taylor & Francis)"

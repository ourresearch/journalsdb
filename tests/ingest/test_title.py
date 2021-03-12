from models.journal import Journal


def test_saved_title(client, run_import_issns_with_api):
    run_import_issns_with_api("ISSN-to-ISSN-L-title.txt")

    j = Journal.query.filter_by(issn_l="2167-0587").one()
    assert j.title == "Journal of geography & natural disasters"

from models.journal import Journal


def test_saved_title(client, run_import_issns_with_api):
    run_import_issns_with_api("ISSN-to-ISSN-L-title.txt")

    j = Journal.query.filter_by(issn_l="0000-0027").one()
    assert j.title == "Library journal."


def test_remove_control_characters(client, run_import_issns_with_api):
    run_import_issns_with_api("ISSN-to-ISSN-L-title.txt")

    j = Journal.query.filter_by(issn_l="2119-8306").one()
    assert j.title == "Les Centralités économiques."

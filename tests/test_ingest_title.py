from ingest.journals.journals_new_journal import NewJournal
from models.journal import ISSNMetaData


def test_clean_title_print():
    issn_md = ISSNMetaData()
    nj = NewJournal(issn_md)
    title_with_print = nj.clean_title("Cooking Today (Print)")
    assert title_with_print == "Cooking Today"


def test_clean_title_electronic():
    issn_md = ISSNMetaData()
    nj = NewJournal(issn_md)
    title_with_electronic = nj.clean_title("Cooking Today   (electronic)")
    assert title_with_electronic == "Cooking Today"


def test_clean_title_trailing_period():
    issn_md = ISSNMetaData()
    nj = NewJournal(issn_md)
    title_with_period = nj.clean_title("Cooking today. ")
    assert title_with_period == "Cooking today"

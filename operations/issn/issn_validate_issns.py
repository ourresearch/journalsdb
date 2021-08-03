import requests

from models.journal import Journal, Publisher


def validate_issns(publisher_id):
    """
    Validates journal ISSNs by finding each ISSN somewhere on the journal's web page.
    Prints any suspect ISSNs that are not found.
    """
    publisher = Publisher.query.get(publisher_id)
    journals = Journal.query.filter_by(publisher=publisher).all()

    for journal in journals:
        metadata = journal.journal_metadata[0] if journal.journal_metadata else None
        if metadata and metadata.home_page_url and publisher.name == "Springer Nature":
            validate_springer_issn(journal)


def validate_springer_issn(journal):
    match = False
    url = journal.journal_metadata[0].home_page_url
    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        return

    if "now archived" in r.text or "ceased" in r.text:
        return

    for issn in journal.issns:
        if issn in r.text:
            match = True

    if not match:
        print(
            "no matching issns found for issn_l {} with issns {} {}".format(
                journal.issn_l, journal.issns, url
            )
        )

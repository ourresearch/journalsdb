from datetime import datetime
import json

import requests

from app import app, db
from models.journal import Journal
from models.usage import Citation


@app.cli.command("import_citations")
def import_citations():
    journals = get_journals()
    for journal in journals:
        dois_by_year = get_dois_by_year(journal.issn_l)
        citations_by_year = get_citation_counts(dois_by_year)
        citations_per_doi = get_citations_per_doi(dois_by_year, citations_by_year)
        save_data(journal.id, citations_by_year, citations_per_doi)


def get_journals():
    subquery = db.session.query(Citation.journal_id)
    return (
        db.session.query(Journal)
        .filter(Journal.publisher_id.in_((11, 16, 20, 29, 36)))
        .filter(Journal.id.notin_(subquery))
        .limit(10000)
        .all()
    )


def get_dois_by_year(issn):
    dois_by_year = {}
    current_year = datetime.now().year
    future_year = current_year + 1
    one_year_ago = current_year - 1
    two_years_ago = current_year - 2
    dois_by_year[current_year] = get_dois(issn, current_year, future_year)
    dois_by_year[one_year_ago] = get_dois(issn, one_year_ago, current_year)
    dois_by_year[two_years_ago] = get_dois(issn, two_years_ago, one_year_ago)
    print(f"done with dois by year for {issn}")
    return dois_by_year


def get_dois(issn, from_year, to_year):
    """
    Returns a list of DOIs for a particular timeframe.
    """
    dois = []
    url = f"https://api.crossref.org/journals/{issn}/works?rows=500&filter=from-pub-date:{from_year}-01-01,until-pub-date:{to_year}-01-01&mailto=team@ourresearch.org"
    r = requests.get(url)
    if r.status_code == 200:
        for article in r.json()["message"]["items"]:
            dois.append(article["DOI"])
    return dois


def get_citation_counts(dois_by_year):
    """
    Get citation counts from opencitations.net.
    Documentation: https://opencitations.net/index/api/v1#/citation-count/{doi}
    Optional https://api.semanticscholar.org/v1/paper/10.1038/nrn3241
    """
    citations_by_year = {}

    for year, dois in dois_by_year.items():
        count = 0
        if dois:
            for doi in dois:
                try:
                    r = requests.get(
                        f"https://opencitations.net/index/coci/api/v1/citation-count/{doi}"
                    )
                    result = int(r.json()[0]["count"])
                    count = count + result
                except json.decoder.JSONDecodeError:
                    print("json error", doi)
            citations_by_year[year] = count
    return citations_by_year


def get_citations_per_doi(dois_by_year, citations_by_year):
    """
    Returns citations per DOI.
    """
    citations_per_doi = {}
    for year, dois in dois_by_year.items():
        if len(dois) > 0:
            citations_per_doi[year] = round(citations_by_year[year] / len(dois), 2)
    return citations_per_doi


def save_data(journal_id, citations_by_year, citations_per_doi):
    if citations_by_year or citations_per_doi:
        c = Citation(
            journal_id=journal_id,
            citations_by_year=citations_by_year,
            citations_per_article=citations_per_doi,
        )
        print(
            f"saving data for journal with id {journal_id} and citations by year {citations_by_year} and citations per article {citations_per_doi}"
        )
        db.session.add(c)
        db.session.commit()

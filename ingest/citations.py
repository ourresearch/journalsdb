from datetime import datetime
import json

import click
import requests

from app import app


@app.cli.command("import_citations")
@click.option("--issn", prompt=True)
def import_citations(issn):
    dois_by_year = get_dois_by_year(issn)
    citations_by_year = get_citation_counts(dois_by_year)
    citations_per_doi = get_citations_per_doi(dois_by_year, citations_by_year)
    print(citations_by_year)
    print(citations_per_doi)


def get_dois_by_year(issn):
    dois_by_year = {}
    current_year = datetime.now().year
    future_year = current_year + 1
    one_year_ago = current_year - 1
    two_years_ago = current_year - 2
    dois_by_year[current_year] = get_dois(issn, current_year, future_year)
    dois_by_year[one_year_ago] = get_dois(issn, one_year_ago, current_year)
    dois_by_year[two_years_ago] = get_dois(issn, two_years_ago, one_year_ago)
    print("done with dois by year")
    return dois_by_year


def get_dois(issn, from_year, to_year):
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
    """
    citations_by_year = {}

    for year, dois in dois_by_year.items():
        count = 0
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
    citations_per_doi = {}
    for year, dois in dois_by_year.items():
        if len(dois) > 0:
            citations_per_doi[year] = citations_by_year[year] / len(dois)
        else:
            citations_per_doi[year] = 0
    return citations_per_doi

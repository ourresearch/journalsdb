from flask import abort, jsonify, request

from app import app
from models.journal import Journal
from models.usage import OpenAccess, Repository
from models.issn import ISSNMetaData
from flasgger import swag_from


@app.route("/")
def index():
    return jsonify(
        {"version": "0.1", "documentation_url": "/apidocs", "msg": "Don't panic"}
    )


@app.route("/journal/<issn_l>/repositories")
def repositories(issn_l):
    repositories = Repository.repositories(issn_l)
    results = [r.to_dict() for r in repositories]

    return jsonify(results)


@app.route("/search/")
@swag_from("docs/search.yml")
def search():
    query = request.args.get("query")
    page = request.args.get("page")
    page = int(page) if page else None
    if not query:
        return jsonify("no results found")
    journals = Journal.query.filter(Journal.title.ilike("%" + query + "%")).paginate(
        page=page, per_page=20
    )
    results = []
    for j in journals.items:
        results.append(
            {
                "issn_l": j.issn_l,
                "journal_title": j.title,
                "publisher": j.publisher.name if j.publisher else None,
            }
        )
    return jsonify(results)


@app.route("/journal/<issn>")
@swag_from("docs/journal.yml")
def journal_detail(issn):
    journal = Journal.find_by_issn(issn)
    metadata = journal.issn_metadata.crossref_raw_api
    dois_by_year, total_dois = process_metadata(metadata)
    if journal:
        journal_dict = build_journal_dict(journal, issn, dois_by_year, total_dois)
    else:
        return abort(404, description="Resource not found")
    return jsonify(journal_dict)


def process_metadata(metadata):
    dois_by_year = metadata["message"]["breakdowns"]["dois-by-issued-year"]
    total_dois = metadata["message"]["counts"]["total-dois"]
    return dois_by_year, total_dois


def build_journal_dict(journal, issn_l, dois_by_year, total_dois):
    journal_dict = journal.to_dict()
    journal_dict["open_access"] = (
        OpenAccess.recent_status(journal.issn_l).to_dict()
        if OpenAccess.recent_status(journal.issn_l)
        else None
    )
    journal_dict["repositories"] = "https://journalsdb.org/" + issn_l + "/repositories"
    journal_dict["readership"] = [e.to_dict() for e in journal.extension_requests]
    journal_dict["author_permissions"] = (
        journal.permissions.to_dict() if journal.permissions else None
    )
    journal_dict["pricing"] = [price.to_dict() for price in journal.subscription_prices]
    journal_dict["dois_by_issued_year"] = dois_by_year
    journal_dict["total_dois"] = total_dois
    return journal_dict


if __name__ == "__main__":
    app.run(host="0.0.0.0")

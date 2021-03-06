from flask import abort, jsonify, request

from app import app, db
from models.journal import Journal, Publisher
from models.usage import OpenAccess, Repository, RetractionSummary
from models.issn import ISSNMetaData
from models.location import Region, Country
from flasgger import swag_from

SITE_URL = "https://journalsdb.org"


@app.route("/")
def index():
    return jsonify(
        {
            "version": "0.1",
            "documentation_url": "{}/apidocs".format(SITE_URL),
            "msg": "Don't panic",
        }
    )


@app.route("/journal/<issn_l>/repositories")
def repositories(issn_l):
    journal = Journal.find_by_issn(issn_l)
    repositories = Repository.repositories(issn_l)
    results = {
        "issn_l": journal.issn_l,
        "journal_title": journal.title,
        "repositories": [r.to_dict() for r in repositories],
    }
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
    if journal:
        metadata = journal.issn_metadata.crossref_raw_api
        dois_by_year, total_dois = process_metadata(metadata)
        journal_dict = build_journal_dict(journal, issn, dois_by_year, total_dois)
    else:
        return abort(404, description="Resource not found")
    return jsonify(journal_dict), 200


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
    journal_dict["repositories"] = "{}/journal/{}/repositories".format(SITE_URL, issn_l)
    journal_dict["readership"] = [e.to_dict() for e in journal.extension_requests]
    journal_dict["author_permissions"] = (
        journal.permissions.to_dict() if journal.permissions else None
    )
    journal_dict["subscription_pricing"] = {
        "provenance": journal.publisher.sub_data_source,
        "prices": sorted(
            [p.to_dict() for p in journal.subscription_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
    }
    journal_dict["apc_pricing"] = {
        "provenance": journal.publisher.sub_data_source,
        "apc_prices": sorted(
            [p.to_dict() for p in journal.apc_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
    }
    journal_dict["retractions"] = RetractionSummary.retractions_by_year(issn_l)
    journal_dict["dois_by_issued_year"] = dois_by_year
    journal_dict["total_dois"] = total_dois
    journal_dict["open_access"] = "{}/open-access/{}".format(SITE_URL, issn_l)
    return journal_dict


@app.route("/open-access/<issn>")
@swag_from("docs/open_access.yml")
def open_access(issn):
    open_access, num_dois, num_green, num_hybrid = get_open_access(issn)
    results = {
        "issn_l": issn,
        "open_access": open_access,
        "summary": {
            "num_dois": num_dois,
            "num_green": num_green,
            "num_hybrid": num_hybrid,
        },
    }
    return jsonify(results), 200


def get_open_access(issn):
    open_access = (
        db.session.query(OpenAccess)
        .filter_by(issn_l=issn)
        .filter(OpenAccess.year > 2009)
        .all()
    )
    results = []
    num_dois = 0
    num_green = 0
    num_hybrid = 0
    for oa in open_access:
        entry = oa.to_dict()
        num_dois += entry["num_dois"]
        num_green += entry["num_green"]
        num_hybrid += entry["num_hybrid"]
        results.append(entry)
    final = sorted(results, key=lambda o: o["year"], reverse=True)
    return final, num_dois, num_green, num_hybrid


if __name__ == "__main__":
    app.run(host="0.0.0.0")

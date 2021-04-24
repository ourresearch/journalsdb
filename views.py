from flask import abort, jsonify, redirect, request, url_for
from flasgger import swag_from
import json

from app import app, cache, db
from models.journal import Journal, Publisher
from models.usage import OpenAccess, Repository, RetractionSummary
from models.issn import ISSNMetaData
from models.location import Region, Country

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


@app.route("/journals")
@cache.cached(timeout=60 * 60 * 6, query_string=True)
@swag_from("docs/journals.yml")
def journals():
    attrs = request.args.get("attrs")
    pub_name = request.args.get("publisher_name")
    filter = {"name": pub_name}
    multi_pubs = True
    if pub_name:
        publishers = (
            db.session.query(Publisher)
            .filter(Publisher.publisher_synonyms.contains(json.dumps(pub_name)))
            .all()
        )
        if not publishers:
            publisher = (
                db.session.query(Publisher).filter_by(name=pub_name).one_or_none()
            )
            multi_pubs = False
            if not publisher:
                return jsonify({"error": "Invalid publisher"}), 400
    if attrs:
        attrs = set(attrs.split(","))
        if not is_valid_attrs(attrs):
            return jsonify({"error": "Invalid attributes"}), 400
        journal_attrs, publisher_attrs, metadata_attrs = process_attrs(attrs)
        journals = get_journals(
            journal_attrs, publisher_attrs, metadata_attrs, filter, multi_pubs
        )
    else:
        column = getattr(Journal, "issn_l")
        journals = db.session.query(Journal).with_entities(column).all()

    journal_results = []
    for j in journals:
        result = j._asdict()

        # handle issns
        if attrs and metadata_attrs and "issns" in metadata_attrs:
            result["issns"] = list(set(result["issn_org_issns"]))
            del result["crossref_issns"]
            del result["issn_org_issns"]

        # set publisher key name
        if attrs and publisher_attrs and "name" in publisher_attrs:
            result["publisher_name"] = result["name"]
            del result["name"]

        journal_results.append(result)

    response = {"journals": journal_results, "count": len(journals)}
    return jsonify(response)


def is_valid_attrs(attrs):
    valid_attrs = {
        "issn_l",
        "journal_synonyms",
        "title",
        "uuid",
        "publisher_name",
        "publisher_synonyms",
        "issns",
    }

    if attrs.difference(valid_attrs):
        is_valid = False
    else:
        is_valid = True
    return is_valid


def process_attrs(attrs):
    valid_journal_attrs = {"issn_l", "journal_synonyms", "title", "uuid"}
    valid_publisher_attrs = {"publisher_name", "publisher_synonyms"}
    valid_metadata_attrs = {"issns"}

    journal_attrs = attrs.intersection(valid_journal_attrs)
    publisher_attrs = attrs.intersection(valid_publisher_attrs)
    publisher_attrs = [a.replace("publisher_name", "name") for a in publisher_attrs]
    metadata_attrs = attrs.intersection(valid_metadata_attrs)
    return journal_attrs, publisher_attrs, metadata_attrs


def get_journals(journal_attrs, publisher_attrs, metadata_attrs, filters, multi_pubs):
    columns = [getattr(Journal, i) for i in journal_attrs]

    if publisher_attrs:
        columns.extend([getattr(Publisher, i) for i in publisher_attrs])

    if "issns" in metadata_attrs:
        metadata_columns = ["issn_org_issns", "crossref_issns"]
        columns.extend([getattr(ISSNMetaData, i) for i in metadata_columns])

    if not multi_pubs:
        return (
            db.session.query(Journal)
            .outerjoin(Journal.publisher)
            .filter_by(**filters)
            .join(Journal.issn_metadata)
            .with_entities(*columns)
            .all()
        )

    if filters["name"]:
        return (
            db.session.query(Journal)
            .join(Journal.publisher)
            .filter(Publisher.publisher_synonyms.contains(json.dumps(filters["name"])))
            .join(Journal.issn_metadata)
            .with_entities(*columns)
            .all()
        )

    return (
        db.session.query(Journal)
        .outerjoin(Journal.publisher)
        .join(Journal.issn_metadata)
        .with_entities(*columns)
        .all()
    )


@app.route("/journals/<issn_l>/repositories")
@swag_from("docs/repositories.yml")
def repositories(issn_l):
    journal = Journal.find_by_issn(issn_l)
    repositories = Repository.repositories(issn_l)
    results = {
        "issn_l": journal.issn_l,
        "journal_title": journal.title,
        "repositories": [r.to_dict() for r in repositories],
    }
    return jsonify(results)


@app.route("/journals/search/")
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


@app.route("/journals/<issn>")
@swag_from("docs/journal.yml")
def journal_detail(issn):
    journal = Journal.query.filter_by(issn_l=issn).one_or_none()

    if not journal:
        # try to find in issn mapping, then redirect to issn_l
        issn_in_issn_org = ISSNMetaData.query.filter(
            ISSNMetaData.issn_org_issns.contains(json.dumps(issn))
        ).first()

        issn_in_crossref = ISSNMetaData.query.filter(
            ISSNMetaData.crossref_issns.contains(json.dumps(issn))
        ).first()

        metadata_record = issn_in_issn_org or issn_in_crossref

        if metadata_record:
            return redirect(url_for("journal_detail", issn=metadata_record.issn_l))
        else:
            # nothing found
            return abort(404, description="Resource not found")

    metadata = journal.issn_metadata.crossref_raw_api
    dois_by_year, total_dois = process_metadata(metadata)
    journal_dict = build_journal_dict(journal, issn, dois_by_year, total_dois)
    return jsonify(journal_dict), 200


def process_metadata(metadata):
    try:
        dois_by_year = metadata["message"]["breakdowns"]["dois-by-issued-year"]
        total_dois = metadata["message"]["counts"]["total-dois"]
    except TypeError:
        dois_by_year = None
        total_dois = None
    return dois_by_year, total_dois


def build_journal_dict(journal, issn_l, dois_by_year, total_dois):
    journal_dict = journal.to_dict()
    journal_dict["open_access"] = (
        OpenAccess.recent_status(journal.issn_l).to_dict()
        if OpenAccess.recent_status(journal.issn_l)
        else None
    )
    journal_dict["repositories"] = "{}/journals/{}/repositories".format(
        SITE_URL, issn_l
    )
    journal_dict["readership"] = [e.to_dict() for e in journal.extension_requests]
    journal_dict["author_permissions"] = (
        journal.permissions.to_dict() if journal.permissions else None
    )
    if journal.journal_metadata:
        journal_dict["journal_metadata"] = [
            m.to_dict() for m in journal.journal_metadata
        ]
    journal_dict["subscription_pricing"] = {
        "provenance": journal.publisher.sub_data_source if journal.publisher else None,
        "prices": sorted(
            [p.to_dict() for p in journal.subscription_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
    }
    journal_dict["apc_pricing"] = {
        "provenance": journal.publisher.apc_data_source if journal.publisher else None,
        "apc_prices": sorted(
            [p.to_dict() for p in journal.apc_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
    }
    journal_dict["retractions"] = RetractionSummary.retractions_by_year(issn_l)
    journal_dict["dois_by_issued_year"] = dois_by_year
    journal_dict["total_dois"] = total_dois
    journal_dict["open_access"] = "{}/journals/{}/open-access".format(SITE_URL, issn_l)
    return journal_dict


@app.route("/journals_full")
def journals_full():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    journals = Journal.query.paginate(page, per_page)

    results = {
        "results": [],
        "pagination": {
            "count": journals.total,
            "page": page,
            "per_page": per_page,
            "pages": journals.pages,
        },
    }

    for j in journals.items:
        metadata = j.issn_metadata.crossref_raw_api
        dois_by_year, total_dois = process_metadata(metadata)
        journal_dict = build_journal_dict(j, j.issn_l, dois_by_year, total_dois)
        results["results"].append(journal_dict)
    return jsonify(results), 200


def process_metadata(metadata):
    try:
        dois_by_year = metadata["message"]["breakdowns"]["dois-by-issued-year"]
        total_dois = metadata["message"]["counts"]["total-dois"]
    except TypeError:
        dois_by_year = None
        total_dois = None
    return dois_by_year, total_dois


def build_journal_dict(journal, issn_l, dois_by_year, total_dois):
    journal_dict = journal.to_dict()
    journal_dict["open_access"] = (
        OpenAccess.recent_status(journal.issn_l).to_dict()
        if OpenAccess.recent_status(journal.issn_l)
        else None
    )
    journal_dict["repositories"] = "{}/journals/{}/repositories".format(
        SITE_URL, issn_l
    )
    journal_dict["readership"] = [e.to_dict() for e in journal.extension_requests]
    journal_dict["author_permissions"] = (
        journal.permissions.to_dict() if journal.permissions else None
    )
    if journal.journal_metadata:
        journal_dict["journal_metadata"] = [
            m.to_dict() for m in journal.journal_metadata
        ]
    journal_dict["subscription_pricing"] = {
        "provenance": journal.publisher.sub_data_source if journal.publisher else None,
        "prices": sorted(
            [p.to_dict() for p in journal.subscription_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
    }
    journal_dict["apc_pricing"] = {
        "provenance": journal.publisher.apc_data_source if journal.publisher else None,
        "apc_prices": sorted(
            [p.to_dict() for p in journal.apc_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
    }
    journal_dict["retractions"] = RetractionSummary.retractions_by_year(issn_l)
    journal_dict["dois_by_issued_year"] = dois_by_year
    journal_dict["total_dois"] = total_dois
    journal_dict["open_access"] = "{}/journals/{}/open-access".format(SITE_URL, issn_l)
    return journal_dict


@app.route("/journals/<issn>/open-access")
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

from flask import abort, jsonify, redirect, request, url_for
from flasgger import swag_from
import json

from app import app, cache, db
from models.journal import Journal, Publisher
from models.usage import OpenAccess, Repository, RetractionSummary
from models.issn import ISSNMetaData, MissingJournal
from models.location import Region, Country

SITE_URL = "https://api.journalsdb.org"


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


@app.route("/journals/search")
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

    journal_dict = build_journal_dict_detail(journal, issn)
    return jsonify(journal_dict), 200


def build_journal_dict_detail(journal, issn_l):
    journal_dict = journal.to_dict()
    journal_dict["journal_metadata"] = (
        [m.to_dict() for m in journal.journal_metadata]
        if journal.journal_metadata
        else []
    )
    dois = journal.doi_counts
    journal_dict["total_dois"] = dois.total_dois if dois else None
    journal_dict["dois_by_issued_year"] = dois.dois_by_year_sorted if dois else None
    journal_dict["sample_dois"] = dois.sample_doi_urls if dois else None
    journal_dict["subscription_pricing"] = {
        "provenance": journal.publisher.sub_data_source if journal.publisher else None,
        "prices": sorted(
            [p.to_dict() for p in journal.subscription_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
        "mini_bundles": [m.to_dict() for m in journal.mini_bundles],
    }
    journal_dict["apc_pricing"] = {
        "provenance": journal.publisher.apc_data_source if journal.publisher else None,
        "apc_prices": sorted(
            [p.to_dict() for p in journal.apc_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
    }
    journal_dict["open_access"] = (
        journal.open_access[0].to_dict() if journal.open_access else None
    )
    journal_dict["open_access_history"] = "{}/journals/{}/open-access".format(
        SITE_URL, issn_l
    )
    journal_dict["repositories"] = "{}/journals/{}/repositories".format(
        SITE_URL, issn_l
    )
    journal_dict["readership"] = [e.to_dict() for e in journal.extension_requests]
    journal_dict["author_permissions"] = (
        journal.permissions.to_dict() if journal.permissions else None
    )
    journal_dict["retractions"] = RetractionSummary.retractions_by_year(issn_l)
    return journal_dict


@app.route("/journals-paged")
def journals_paged():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per-page", 100, type=int)

    journals = Journal.query.order_by(Journal.created_at.asc()).paginate(page, per_page)

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
        journal_dict = build_journal_dict_paged(j)
        results["results"].append(journal_dict)

    base_url = SITE_URL + "/journals-paged"
    link_header = build_link_header(
        query=journals, base_url=base_url, per_page=per_page
    )
    return jsonify(results), 200, link_header


def build_journal_dict_paged(journal):
    journal_dict = journal.to_dict()
    journal_dict["journal_metadata"] = (
        [m.to_dict() for m in journal.journal_metadata]
        if journal.journal_metadata
        else []
    )
    dois = journal.doi_counts
    journal_dict["total_dois"] = dois.total_dois if dois else None
    journal_dict["dois_by_issued_year"] = dois.dois_by_year_sorted if dois else None
    journal_dict["sample_dois"] = dois.sample_doi_urls if dois else None
    journal_dict["subscription_pricing"] = {
        "provenance": journal.publisher.sub_data_source if journal.publisher else None,
        "prices": sorted(
            [p.to_dict() for p in journal.subscription_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
        "mini_bundles": [m.to_dict() for m in journal.mini_bundles],
    }
    journal_dict["apc_pricing"] = {
        "provenance": journal.publisher.apc_data_source if journal.publisher else None,
        "apc_prices": sorted(
            [p.to_dict() for p in journal.apc_prices],
            key=lambda p: p["year"],
            reverse=True,
        ),
    }
    journal_dict["open_access"] = (
        journal.open_access[0].to_dict() if journal.open_access else None
    )
    return journal_dict


def build_link_header(query, base_url, per_page):
    links = [
        '<{0}?page=1&per-page={1}>; rel="first"'.format(base_url, per_page),
        '<{0}?page={1}&per-page={2}>; rel="last"'.format(
            base_url, query.pages, per_page
        ),
    ]
    if query.has_prev:
        links.append(
            '<{0}?page={1}&per-page={2}>; rel="prev"'.format(
                base_url, query.prev_num, per_page
            )
        )
    if query.has_next:
        links.append(
            '<{0}?page={1}&per-page={2}>; rel="next"'.format(
                base_url, query.next_num, per_page
            )
        )

    links = ",".join(links)
    return dict(Link=links)


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


@app.route("/missing_journal", methods=["POST"])
def missing_journal():
    if not request.json or "issn" not in request.json:
        abort(400)

    posted_data = request.get_json()
    issn = posted_data["issn"]
    if (
        Journal.find_by_issn(issn)
        or MissingJournal.query.filter_by(issn=issn).one_or_none()
    ):
        return jsonify({"Message": "issn already exists"}), 200
    else:
        missing_journal = MissingJournal(issn=issn)
        db.session.add(missing_journal)
        db.session.commit()
        return jsonify({"Missing journal created": missing_journal.issn}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0")

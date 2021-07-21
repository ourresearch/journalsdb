import json

from flask import abort, jsonify, redirect, request, url_for
from flasgger import swag_from
from sqlalchemy.orm import joinedload

from app import app, cache, db
from models.journal import Journal, Publisher
from models.usage import OpenAccess, Repository
from models.issn import ISSNMetaData, MissingJournal
from schemas.schema_combined import JournalDetailSchema, JournalListSchema
from utils import (
    build_link_header,
    get_publisher_ids,
    process_only_fields,
    validate_status,
)

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


@app.route("/journals/<issn>")
@swag_from("docs/journal.yml")
def journal_detail(issn):
    redirect_param = request.args.get("redirect", "true", type=str)
    redirect_param = json.loads(redirect_param)  # convert 'true' to True

    journal = Journal.find_by_issn(issn)

    if not journal:
        return abort(404, description="Resource not found")

    elif journal.current_journal and redirect_param:
        # more recent version of the journal exists, so we should redirect to it
        return redirect(url_for("journal_detail", issn=journal.current_journal.issn_l))

    elif journal.issn_l != issn and issn in journal.issns:
        # redirect to primary issn_l
        return redirect(url_for("journal_detail", issn=journal.issn_l))

    journal_detail_schema = JournalDetailSchema()
    return journal_detail_schema.dump(journal)


@app.route("/journals-paged")
def journals_paged():
    # process query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per-page", 100, type=int)
    attrs = request.args.get("attrs")
    only = process_only_fields(attrs) if attrs else None
    publishers = request.args.get("publishers")
    publisher_ids = get_publisher_ids(publishers) if publishers else []
    valid_status = validate_status(request.args.get("status"))

    # primary query
    journals = (
        Journal.query.order_by(Journal.created_at.asc())
        .options(joinedload(Journal.doi_counts))
        .options(joinedload(Journal.issn_metadata))
        .options(joinedload(Journal.journal_metadata))
        .options(joinedload(Journal.open_access))
    )

    # filters
    if publisher_ids:
        journals = journals.filter(Journal.publisher_id.in_(publisher_ids))

    if valid_status:
        journals = journals.filter_by(status=valid_status)

    # pagination
    journals = journals.paginate(page, per_page)

    # schema with displayed fields based on attrs
    journal_list_schema = JournalListSchema(only=only)
    journals_dumped = journal_list_schema.dump(journals.items, many=True)

    # combined results with pagination
    results = {
        "results": journals_dumped,
        "pagination": {
            "count": journals.total,
            "page": page,
            "per_page": per_page,
            "pages": journals.pages,
        },
    }

    # paginated link headers
    base_url = SITE_URL + "/journals-paged"
    link_header = build_link_header(
        query=journals, base_url=base_url, per_page=per_page
    )
    return jsonify(results), 200, link_header


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
    if Journal.find_by_issn(issn):
        journal = MissingJournal(issn=issn, status="already in database")
        message = "{} issn already in database, marking as submitted".format(issn)
    elif MissingJournal.query.filter_by(issn=issn).all():
        journal = MissingJournal(issn=issn, status="already submitted")
        message = "{} issn already submitted, marking as already submitted".format(issn)
    else:
        journal = MissingJournal(issn=issn, status="process")
        message = "{} issn submitted for processing".format(issn)

    db.session.add(journal)
    db.session.commit()
    return jsonify({"message": message}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0")

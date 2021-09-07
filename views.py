from flask import abort, jsonify, redirect, request, url_for
from flasgger import swag_from

from app import app, db
from exceptions import APIError
from models.journal import Journal
from models.usage import OpenAccess, Repository
from models.issn import MissingJournal
from schemas.schema_combined import JournalDetailSchema, JournalListSchema
from utils import (
    build_link_header,
    get_publisher_ids,
    process_only_fields,
    validate_per_page,
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
    journal = Journal.find_by_issn(issn)

    if not journal:
        return abort(404, description="Resource not found")

    elif journal.issn_l != issn and issn in journal.issns:
        # redirect to primary issn_l
        return redirect(url_for("journal_detail", issn=journal.issn_l))

    journal_detail_schema = JournalDetailSchema()
    return journal_detail_schema.dump(journal)


@app.route("/journals-paged")
@app.route("/journals")
@swag_from("docs/journals.yml")
def journals_paged():
    # process query parameters
    page = request.args.get("page", 1, type=int)
    per_page = validate_per_page(request.args.get("per-page", 100, type=int))
    attrs = request.args.get("attrs")
    only = process_only_fields(attrs) if attrs else None
    publishers = request.args.get("publishers")
    publisher_ids = get_publisher_ids(publishers) if publishers else []
    valid_status = validate_status(request.args.get("status"))

    # primary query
    journals = Journal.query.order_by(Journal.created_at.asc())

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


@app.errorhandler(APIError)
def handle_exception(err):
    """Return custom JSON when APIError or its children are raised"""
    response = {"error": err.description, "message": ""}
    if len(err.args) > 0:
        response["message"] = err.args[0]
    # Add some logging so that we can monitor different types of errors
    app.logger.error("{}: {}".format(err.description, response["message"]))
    return jsonify(response), err.code


if __name__ == "__main__":
    app.run(host="0.0.0.0")

from flask import abort, jsonify, request

from app import app
from models.journal import Journal
from models.usage import OpenAccess


@app.route("/")
def index():
    return jsonify({"version": "0.1", "documentation_url": "TBD", "msg": "Don't panic"})


@app.route("/search/")
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
def journal_detail(issn):
    journal = Journal.find_by_issn(issn)
    if journal:
        journal_dict = build_journal_dict(journal)
    else:
        return abort(404, description="Resource not found")
    return jsonify(journal_dict)


def build_journal_dict(journal):
    journal_dict = journal.to_dict()
    journal_dict["open_access_status"] = OpenAccess.recent_status(
        journal.issn_l
    ).to_dict()
    journal_dict["repositories"] = [
        repository.to_dict() for repository in journal.repositories[:20]
    ]
    journal_dict["readership"] = [e.to_dict() for e in journal.extension_requests]
    journal_dict["author_permissions"] = (
        journal.permissions.to_dict() if journal.permissions else None
    )
    journal_dict["pricing"] = [price.to_dict() for price in journal.subscription_prices]
    return journal_dict


if __name__ == "__main__":
    app.run(host="0.0.0.0")

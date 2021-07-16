import datetime
import json

import requests
from sqlalchemy import exc

from app import app, db
from ingest.utils import get_or_create, remove_control_characters
from models.issn import (
    ISSNMetaData,
    LinkedISSNL,
)
from models.journal import Journal, Publisher


@app.cli.command("import_issn_apis")
def import_issn_apis():
    """
    Iterate over issn_metadata table, then fetch and store API data from issn.org and crossref.
    Save title and publisher to journals table.
    """
    issns = ISSNMetaData.query.filter_by(updated_at=None).all()

    for issn in issns:
        save_issn_org_api(issn)
        save_crossref_api(issn)
        save_journal_with_title(issn)
        set_publisher(issn)
        link_issn_l(issn)

        # set updated_at
        issn.updated_at = datetime.datetime.now()
        db.session.commit()


def save_issn_org_api(issn):
    issn_org_url = "https://portal.issn.org/resource/ISSN/{}?format=json".format(
        issn.issn_l
    )
    try:
        r = requests.get(issn_org_url)
        if r.status_code == 200 and "@graph" in r.json():
            issn.issn_org_raw_api = r.json()
            db.session.commit()
            print("saving issn org data for issn {}".format(issn.issn_l))
        else:
            print("no issn org data found for {}".format(issn.issn_l))
    except (requests.exceptions.ConnectionError, json.JSONDecodeError):
        return


def save_crossref_api(issn):
    crossref_url = "https://api.crossref.org/journals/{}".format(issn.issn_l)
    try:
        r = requests.get(crossref_url)
        if r.status_code == 200:
            issn.crossref_raw_api = r.json()
            issn.crossref_issns = issn.issns_from_crossref_api
            db.session.commit()
            print("saving crossref data for issn {}".format(issn.issn_l))
        else:
            print("no crossref data for issn {}".format(issn.issn_l))
    except requests.exceptions.ConnectionError:
        return None


def save_journal_with_title(issn):
    try:
        j = Journal.query.filter_by(issn_l=issn.issn_l).one_or_none()
        title = remove_control_characters(issn.title_from_issn_api)
        if title and title[-1] == ".":
            title = title[:-1]
        if j and title and not j.is_modified_title:
            # update
            j.title = title
            print("setting journal title to {}".format(title))
        elif title:
            j = Journal(issn_l=issn.issn_l, title=title)
            db.session.add(j)
            db.session.commit()
            print(
                "added new journal with issn_l {} and title {}".format(
                    issn.issn_l, title
                )
            )
    except exc.IntegrityError:
        db.session.rollback()
        return


def set_publisher(issn):
    try:
        publisher = (
            get_or_create(db.session, Publisher, name=issn.publisher)
            if issn.publisher
            else None
        )
        j = Journal.query.filter_by(issn_l=issn.issn_l).one_or_none()
        if j and publisher:
            j.publisher_id = publisher.id
            print("setting journal {} with publisher {}".format(j.issn_l, publisher))
        db.session.commit()
    except exc.IntegrityError:
        db.session.rollback()
        return


def link_issn_l(issn):
    try:
        # if the issn_l is in a different record issn, then link it
        issn_l_in_crossref_issns = ISSNMetaData.query.filter(
            ISSNMetaData.crossref_issns.contains(json.dumps(issn.issn_l))
        ).all()
        for issn_l_in_crossref in issn_l_in_crossref_issns:
            if issn_l_in_crossref.issn_l != issn.issn_l:
                db.session.add(
                    LinkedISSNL(
                        issn_l_primary=issn.issn_l,
                        issn_l_secondary=issn_l_in_crossref.issn_l,
                        reason="crossref",
                    )
                )
            db.session.commit()
    except exc.IntegrityError:
        db.session.rollback()
        return

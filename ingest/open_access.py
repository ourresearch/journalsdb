import pandas as pd

from app import app, db
from ingest.utils import find_journal
from models.usage import OpenAccessPublishing, OpenAccessStatus


@app.cli.command("import_open_access")
def import_open_access():
    """
    Open access data: https://api.unpaywall.org/journal_open_access.csv.gz

    Counts the number of articles with each oa_status by (issn_l, year).
    num_open = num_green + num_bronze + num_hybrid + num_gold
    {status}_rate = num_{status} / num_dois

    issn_l (string, pkey)
    title (string, nullable)
    year (integer, pkey)
    num_dois (integer)
    num_open (integer)
    open_rate (double precision)
    num_green (integer)
    green_rate (double precision)
    num_bronze (integer)
    bronze_rate (double precision)
    num_hybrid (integer)
    hybrid_rate (double precision)
    num_gold (integer)
    gold_rate (double precision)
    is_in_doaj (boolean)
    is_gold_journal (boolean)

    Run with: flask import_open_access
    """
    url = "https://api.unpaywall.org/journal_open_access.csv.gz"
    df = pd.read_csv(url, compression="gzip", keep_default_na=False)

    for row in df.to_dict(orient="records"):
        if not valid_oa_data(row):
            continue

        # oa status
        journal = find_journal(row["issn_l"])
        existing_oa_status = OpenAccessStatus.query.filter_by(
            journal_id=journal.id, year=(int(row["year"]))
        ).one_or_none()

        if existing_oa_status:
            update_existing_oa_status(existing_oa_status, row)
        else:
            save_new_oa_status(journal, row)

        # oa publishing
        existing_oa_publishing = OpenAccessPublishing.query.filter_by(
            journal_id=journal.id, year=(int(row["year"]))
        ).one_or_none()

        if existing_oa_publishing:
            update_existing_oa_publishing(existing_oa_publishing, row)
        else:
            save_new_oa_publishing(journal, row)

        db.session.commit()


def valid_oa_data(row):
    if not row["issn_l"] or not row["year"]:
        return False
    else:
        return True


def update_existing_oa_status(status, row):
    status.is_in_doaj = row["is_in_doaj"]
    status.is_gold_journal = row["is_gold_journal"]


def save_new_oa_status(journal, row):
    if not journal:
        print("Journal not found for open access data")
        return

    oa_status = OpenAccessStatus(
        journal_id=journal.id,
        is_in_doaj=row["is_in_doaj"],
        is_gold_journal=row["is_gold_journal"],
        year=row["year"],
    )
    db.session.add(oa_status)


def update_existing_oa_publishing(pub, row):
    # remove status fields
    fields_to_remove = ["is_in_doaj", "is_gold_journal", "issn_l", "title"]
    for field in fields_to_remove:
        row.pop(field)

    # update remaining fields
    for key, value in row.iteritems():
        setattr(pub, key, value)


def save_new_oa_publishing(journal, row):
    if not journal:
        print("Journal not found for open access data")
        return

    fields_to_remove = ["is_in_doaj", "is_gold_journal", "issn_l", "title"]
    for field in fields_to_remove:
        row.pop(field)

    # save remaining fields to new object
    oa_publishing = OpenAccessPublishing(**row, journal_id=journal.id)

    db.session.add(oa_publishing)

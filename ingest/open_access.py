import json

import pandas as pd

from app import app, db
from ingest.utils import find_journal
from models.usage import OpenAccess


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
    for chunk in pd.read_csv(
        url, compression="gzip", keep_default_na=False, chunksize=10000
    ):
        new_records = []
        updated_records = []
        for row in chunk.to_dict(orient="records"):
            if OpenAccess.query.filter_by(
                hash=json.dumps(row, sort_keys=True)
            ).one_or_none():
                continue

            if not valid_data(row):
                continue

            # oa status
            journal = find_journal(row["issn_l"])
            existing_oa = OpenAccess.query.filter_by(
                journal_id=journal.id, year=(int(row["year"]))
            ).one_or_none()

            if existing_oa:
                update_existing_oa(existing_oa, row)
            else:
                new_records.append(new_oa(journal, row))

        db.session.bulk_insert_mappings(OpenAccess, new_records)
        db.session.commit()


def valid_data(row):
    if not row["issn_l"] or not row["year"]:
        return False
    else:
        return True


def update_existing_oa(oa, row):
    print("updating record {}".format(oa))
    # update hash
    oa.hash = json.dumps(row, sort_keys=True)

    # remove fields
    fields_to_remove = ["issn_l", "title"]
    for field in fields_to_remove:
        row.pop(field)

    # update remaining fields
    for key, value in row.items():
        setattr(oa, key, value)


def new_oa(journal, row):
    if not journal:
        print("Journal not found for open access data")
        return

    hash_key = json.dumps(row, sort_keys=True)

    fields_to_remove = ["issn_l", "title"]
    for field in fields_to_remove:
        row.pop(field)

    # return remaining fields
    return dict(**row, hash=hash_key, journal_id=journal.id)

import json

import pandas as pd

from app import app, db
from ingest.utils import get_or_create
from models.journal import Journal, Publisher


@app.cli.command("import_journals")
def import_journals():
    """
    Journal metadata: https://api.unpaywall.org/journals.csv.gz

    issn_l (string, pkey)
    issns (json formatted string array)
    publisher (string, nullable)
    title (string, nullable)

    Run with: flask import_journals
    """
    url = "https://api.unpaywall.org/journals.csv.gz"
    df = pd.read_csv(url, compression="gzip", keep_default_na=False)

    for index, row in df.iterrows():
        if not valid_journal_data(row):
            continue

        publisher = (
            get_or_create(db.session, Publisher, name=row["publisher"])
            if row["publisher"]
            else None
        )
        existing_journal = Journal.query.filter_by(issn_l=row["issn_l"]).one_or_none()

        if existing_journal:
            update_existing_journal(existing_journal, publisher, row)
        else:
            save_new_journal(publisher, row)


def valid_journal_data(row):
    if not row["title"] or not row["issn_l"]:
        return False
    else:
        return True


def update_existing_journal(journal, publisher, row):
    journal.title = row["title"]
    journal.publisher = publisher
    journal.issns = json.loads(row["issns"])
    db.session.commit()


def save_new_journal(publisher, row):
    new_journal = Journal(
        issn_l=row["issn_l"],
        issns=json.loads(row["issns"]),
        publisher=publisher,
        title=row["title"],
    )
    db.session.add(new_journal)
    db.session.commit()

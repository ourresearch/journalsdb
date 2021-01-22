import pandas as pd

from app import app, db
from ingest.utils import find_journal
from models.usage import ExtensionRequests


@app.cli.command("import_extension_requests")
def import_extension_requests():
    """
    Extension requests: https://api.unpaywall.org/extension_requests.csv.gz

    Counts the number of API requests for articles published in each journal, by month.
    Will be populated back to 2019-12-01.

    month (timestamp, pkey)
    issn_l (string, pkey)
    requests (integer)

    Run with: flask import_extension_requests
    """
    url = "https://api.unpaywall.org/extension_requests.csv.gz"
    df = pd.read_csv(url, compression="gzip", keep_default_na=False)

    for index, row in df.iterrows():
        if not valid_extension_data(row):
            continue

        journal = find_journal(row["issn_l"])
        if not journal:
            print("journal with issn-l {} not found.".format(row["issn_l"]))
        elif timestamp_exists(journal, row):
            update_existing_timestamp(journal, row)
        else:
            save_new_extension_data(journal, row)


def valid_extension_data(row):
    if not row["issn_l"]:
        print("invalid data in row {}".format(row))
        return False
    else:
        return True


def timestamp_exists(journal, row):
    return ExtensionRequests.query.filter_by(
        month=row["month"], journal=journal
    ).one_or_none()


def update_existing_timestamp(journal, row):
    e = ExtensionRequests.query.filter_by(
        month=row["month"], journal=journal
    ).one_or_none()
    e.requests = row["requests"]
    db.session.commit()


def save_new_extension_data(journal, row):
    new_extension_data = ExtensionRequests(
        month=row["month"], requests=row["requests"], journal=journal
    )
    db.session.add(new_extension_data)
    db.session.commit()

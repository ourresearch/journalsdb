import pandas as pd

from app import app, db
from ingest.utils import find_journal
from models.usage import Repository


@app.cli.command("import_repositories")
def import_repositories():
    """
    Repository article counts: https://api.unpaywall.org/repositories.csv.gz

    issn_l (string, pkey)
    endpoint_id (string, pkey)
    repository_name  (string, nullable)
    institution_name (string, nullable)
    home_page (string, nullable)
    pmh_url (string, nullable)
    num_articles (integer)

    Run with: flask import_repositories
    """
    url = "https://api.unpaywall.org/repositories.csv.gz"
    df = pd.read_csv(url, compression="gzip", keep_default_na=False)

    for index, row in df.iterrows():
        if not valid_repository_data(row):
            continue

        journal = find_journal(row["issn_l"])
        if not journal:
            print("journal with issn-l {} not found.".format(row["issn_l"]))
        elif endpoint_exists(journal, row):
            update_existing_endpoint(journal, row)
        else:
            save_new_repository(journal, row)


def valid_repository_data(row):
    if not row["issn_l"]:
        print("invalid data in row {}".format(row))
        return False
    else:
        return True


def endpoint_exists(journal, row):
    return Repository.query.filter_by(
        endpoint_id=row["endpoint_id"], journal=journal
    ).one_or_none()


def update_existing_endpoint(journal, row):
    endpoint = Repository.query.filter_by(
        endpoint_id=row["endpoint_id"], journal=journal
    ).one_or_none()
    for key, value in row.iteritems():
        setattr(endpoint, key, value)
    db.session.commit()


def save_new_repository(journal, row):
    row.pop("issn_l")
    new_repository = Repository(**row, journal=journal)
    db.session.add(new_repository)
    db.session.commit()

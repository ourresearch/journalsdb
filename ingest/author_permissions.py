import pandas as pd

from app import app, db
from models.journal import Journal
from models.author_permissions import AuthorPermissions


@app.cli.command("import_author_permissions")
def import_author_permissions():
    """
    Google sheet from https://shareyourpaper.org/permissions/about#data

    Run with: flask import_permissions
    """
    url = "https://docs.google.com/spreadsheets/d/{key}/export?format=csv&gid={tab_id}".format(
        key="1nvsAcDQnnIXI1LmzPHA8d4KGNO1PZZF-iMQE7AZaN2s",
        tab_id="1540153499",
    )
    df = pd.read_csv(url, keep_default_na=False)
    df.rename(
        columns=lambda x: x.replace("(s)", "")
        .strip("?")
        .lower()
        .replace(" ", "_")
        .replace("-", "_"),
        inplace=True,
    )  # convert column names from Has Policy? to has_policy

    rows = df.to_dict(orient="records")
    for row in rows:
        if not valid_data(row):
            continue

        row = clean_data(row)
        journal = find_journal(row)

        if not journal:
            print("journal with issn {} not found.".format(row["id"]))
        elif permissions_exists(journal):
            update_existing_permissions(journal, row)
        else:
            save_new_permission(journal, row)

    db.session.commit()


def valid_data(row):
    if (
        type(row["post_print_embargo"]) is not int
        and row["post_print_embargo"].isnumeric() is False
        or row["id"] is None
    ):
        return False
        print("invalid data in row", dict(row))
    else:
        return True


def clean_data(row):
    """
    Convert has_policy to boolean.
    """
    if row["has_policy"].strip() == "Yes":
        row["has_policy"] = True
    return row


def find_journal(row):
    """
    The id field can be a single issn: 2153-0696 or two issns separated by a comma: 0304-3959, 1872-6623.
    Search with one or both by issn-l and issn to find a match.
    """
    journal = None
    issns = row["id"].split(",")
    for issn in issns:
        journal = Journal.query.filter_by(
            issn_l=issn.strip()
        ).one_or_none() or Journal.find_by_issn(issn.strip())
        if journal:
            break
    return journal


def permissions_exists(journal):
    return AuthorPermissions.query.filter_by(journal_id=journal.id).one_or_none()


def update_existing_permissions(journal, row):
    permission = AuthorPermissions.query.filter_by(journal_id=journal.id).one_or_none()
    columns = AuthorPermissions.__table__.columns._data.keys()
    fields_to_ignore = ["id", "journal_id", "created_at", "updated_at"]
    for column in columns:
        if column in fields_to_ignore:
            continue
        else:
            setattr(permission, column, row[column])


def save_new_permission(journal, row):
    columns = AuthorPermissions.__table__.columns._data.keys()
    new_permission = AuthorPermissions()
    fields_to_ignore = ["id", "created_at", "updated_at"]
    for column in columns:
        if column == "journal_id":
            new_permission.journal_id = journal.id
        elif column in fields_to_ignore:
            continue
        else:
            setattr(new_permission, column, row[column])
    db.session.add(new_permission)

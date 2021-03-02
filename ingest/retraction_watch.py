import time

import boto3
import pandas as pd
import requests
from sqlalchemy import exc, extract, func

from app import app, db
from models.journal import Journal
from models.usage import RetractionSummary, RetractionWatch


@app.cli.command("import_retraction_watch")
def import_retraction_watch():
    """
    Imports retraction data from S3.

    Run with: flask import_retraction_watch
    """
    file = get_recent_file()
    df = pd.read_csv("s3://journalsdb/{}".format(file), encoding="ISO-8859-1")

    for index, row in df.iterrows():
        if not db.session.query(RetractionWatch).get(row["Record ID"]):
            crossref_doi_api = call_crossref_api(row["OriginalPaperDOI"])
            r = RetractionWatch(
                record_id=row["Record ID"],
                title=row["Title"],
                journal=row["Journal"],
                publisher=row["Publisher"],
                retraction_date=row["RetractionDate"],
                retraction_doi=row["RetractionDOI"],
                paper_doi=row["OriginalPaperDOI"],
                published_year=get_published_year(crossref_doi_api),
                issn=get_issn(crossref_doi_api),
            )
            print("adding doi {}".format(row["OriginalPaperDOI"]))
            db.session.add(r)
            db.session.commit()


def call_crossref_api(doi):
    """
    Calls the crossref works API for a given DOI.
    """
    url = "http://api.crossref.org/works/{}".format(doi)
    headers = {
        "User-Agent": "JournalsDB/1.1 (https://journalsdb.org; mailto:team@ourresearch.org)"
    }
    r = requests.get(url, headers=headers)
    time.sleep(0.2)
    return r


def get_published_year(r):
    """
    Look up ISSN via crossref metadata api.
    """
    if r.status_code == 200:
        message = r.json()["message"]
        return message["issued"]["date-parts"][0][0] if message.get("issued") else None
    else:
        print("year not found")
        return None


def get_issn(r):
    """
    Look up ISSN via crossref metadata api.
    """
    if r.status_code == 200:
        message = r.json()["message"]
        return message["ISSN"][0] if message.get("ISSN") else None
    else:
        print("issn not found")
        return None


def get_recent_file():
    """
    Returns the most recently modified file from an S3 bucket.
    """
    bucket = "journalsdb"
    get_last_modified = lambda obj: int(obj["LastModified"].strftime("%s"))
    s3 = boto3.client("s3")
    objs = s3.list_objects_v2(Bucket=bucket)["Contents"]
    last_added = [obj["Key"] for obj in sorted(objs, key=get_last_modified)][0]
    return last_added


@app.cli.command("build_retraction_summary")
def build_retraction_summary():
    """
    Goes through retraction watch data and builds a summary table that can be used to calculate a retraction percentage.

    Run with: flask build_retraction_summary
    """
    retractions = (
        db.session.query(
            RetractionWatch.journal,
            RetractionWatch.issn,
            RetractionWatch.published_year,
            func.count(RetractionWatch.record_id).label("count"),
        )
        .group_by(
            RetractionWatch.issn,
            RetractionWatch.published_year,
            RetractionWatch.journal,
        )
        .all()
    )

    for r in retractions:
        journal = Journal.find_by_issn(r.issn)
        if not journal:
            continue
        metadata = journal.issn_metadata.crossref_raw_api
        if not metadata:
            continue

        dois_by_year = metadata["message"]["breakdowns"]["dois-by-issued-year"]

        for year, num_dois in dois_by_year:
            if year == int(r.year):
                s = RetractionSummary(
                    issn=r.issn,
                    journal=r.journal,
                    year=int(r.year),
                    retractions=r.count,
                    num_dois=num_dois,
                )
                try:
                    db.session.add(s)
                    db.session.commit()
                except exc.IntegrityError:
                    # handle issn, year already exists
                    # need to change to update the row instead
                    db.session.rollback()

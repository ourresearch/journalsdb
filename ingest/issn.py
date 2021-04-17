import os
import datetime
from io import BytesIO
import json
from urllib.request import urlopen
from zipfile import ZipFile

import click
import pandas as pd
import requests
from sqlalchemy import exc, func

from app import app, db
from models.issn import (
    ISSNHistory,
    ISSNMetaData,
    ISSNTemp,
    ISSNToISSNL,
    LinkedISSNL,
    CrossrefTemp,
)
from models.journal import Journal, Publisher
from ingest.utils import get_or_create, remove_control_characters

from csv import reader


@app.cli.command("import_issns")
@click.option("--file_path")
@click.option("--initial_load", is_flag=True)
def import_issns(file_path, initial_load):
    """
    Master ISSN list: https://www.issn.org/wp-content/uploads/2014/03/issnltables.zip
    Available via a text file within the zip archive with name ISSN-to-ISSN-L-initial.txt.

    Read the issn-l to issn mapping from issn.org and save it to a table for further processing.

    Run with: flask import_issns
    """
    zip_url = "https://www.issn.org/wp-content/uploads/2014/03/issnltables.zip"
    issn_tsv_file = get_zipfile(zip_url) if not file_path else file_path

    # ensure temp ISSN temp table is empty
    clear_issn_temp_table()

    # copy issn records into temp table
    copy_tsv_to_temp_table(file_path, issn_tsv_file)

    # sanity check
    if not file_path and ISSNTemp.query.count() < 2000000:
        print("not enough records in file")
        clear_issn_temp_table()

    # if initial load, simply copy the rows to the master issn_to_issnl table and map the issns
    elif initial_load:
        db.session.execute(
            "INSERT INTO issn_to_issnl (issn, issn_l, created_at) SELECT issn, issn_l, NOW() FROM issn_temp;"
        )
        if not "PYTEST_CURRENT_TEST" in os.environ:
            filter_to_crossref_only()
        map_issns_to_issnl()
        # finished, remove temp data
        clear_issn_temp_table()

    else:
        if not "PYTEST_CURRENT_TEST" in os.environ:
            print("filtering to crossref")
            filter_to_crossref_only()
        # compare the regular ISSNtoISSNL table
        # new ISSN records (in temp but not in ISSNtoISSNL)
        new_records = db.session.execute(
            "SELECT issn, issn_l FROM issn_temp EXCEPT SELECT issn, issn_l FROM issn_to_issnl;"
        )
        save_new_records(new_records)

        # removed records (in ISSNtoISSNL but not in issn_temp)
        removed_records = db.session.execute(
            "SELECT issn, issn_l FROM issn_to_issnl EXCEPT SELECT issn, issn_l FROM issn_temp;"
        )
        remove_records(removed_records)

        map_issns_to_issnl()

        # finished, remove temp data
        clear_issn_temp_table()


@app.cli.command("remove_issns")
@click.option("--file_path")
def remove_issns(file_path):
    """
    Takes a CSV file with each row containing an ISSN_L. Removes these ISSN_L entries
    from the ISSNMetaData table.
    Run with: flask remove_issns --file_path filename
    """
    issns_to_keep = set()

    with open(file_path, "r") as file:
        csv_reader = reader(file)
        for row in csv_reader:
            issns_to_keep.add(row[0])  # rows are lists, 0 position is the value

    all_issns = set(
        [entry.issn_l for entry in db.session.query(ISSNMetaData).distinct()]
    )

    print(len(issns_to_keep))
    print(len(all_issns))
    issns_to_remove = all_issns - issns_to_keep
    print(len(issns_to_remove))

    deletion = ISSNMetaData.__table__.delete().where(
        ISSNMetaData.issn_l.in_(issns_to_remove)
    )
    db.session.execute(deletion)
    db.session.commit()


def clear_issn_temp_table():
    db.session.query(ISSNTemp).delete()
    db.session.commit()


def get_zipfile(zip_url):
    """
    Fetches the remote zip file.
    """
    resp = urlopen(zip_url)
    zipfile = ZipFile(BytesIO(resp.read()))
    file_name = find_file_name(zipfile)
    issn_tsv_file = zipfile.open(file_name)
    return issn_tsv_file


def find_file_name(zipfile):
    """
    Finds file from the zip archive ending with issn-to-issn-l.txt.
    """
    files = zipfile.namelist()
    select_file = [f for f in files if f.lower().endswith("issn-to-issn-l.txt")]
    file = select_file[0] if select_file else None
    return file


def copy_tsv_to_temp_table(file_path, issn_file):
    """
    Very fast way to copy 1 million or more rows into a table.
    """
    copy_sql = "COPY issn_temp FROM STDOUT WITH (FORMAT CSV, DELIMITER '\t', HEADER)"
    conn = db.engine.raw_connection()
    with conn.cursor() as cur:
        if not file_path:
            cur.copy_expert(copy_sql, issn_file)
        else:
            # used with test files
            with open(file_path, "rb") as f:
                cur.copy_expert(copy_sql, f)
    conn.commit()


def save_new_records(new_records):
    objects = []
    history = []
    for new in new_records:
        objects.append(
            ISSNToISSNL(
                issn=new.issn,
                issn_l=new.issn_l,
            )
        )
        history.append(ISSNHistory(issn=new.issn, issn_l=new.issn_l, status="added"))
    db.session.bulk_save_objects(objects)
    db.session.bulk_save_objects(history)
    db.session.commit()


def remove_records(removed_records):
    """
    Add to history table but do not delete.
    """
    for removed in removed_records:
        existing = ISSNHistory.query.filter_by(
            issn_l=removed.issn_l, issn=removed.issn, status="removed"
        ).one_or_none()
        if not existing:
            db.session.add(
                ISSNHistory(issn_l=removed.issn_l, issn=removed.issn, status="removed")
            )
    db.session.commit()


def map_issns_to_issnl():
    """
    Map issn-l to issns that are in the issn_to_issnl table.
    """
    sql = """
    insert into issn_metadata (issn_l, issn_org_issns) (
        select
            issn_l,
            jsonb_agg(to_jsonb(issn)) as issn_org_issns
        from issn_to_issnl
        where issn_l is not null
        group by 1
    ) on conflict (issn_l) do update
    set issn_org_issns = excluded.issn_org_issns;
    """
    db.session.execute(sql)
    db.session.commit()


def filter_to_crossref_only():
    """
    Filter issn_to_issnl table so it only has ISSNs that are in crossref.
    https://api.unpaywall.org/crossref_issns.csv.gz
    """
    file = urlopen("https://api.unpaywall.org/crossref_issns.csv.gz")
    data = pd.read_csv(file, compression="gzip")
    crossref_issns = data["issn"].tolist()
    for issn in crossref_issns:
        if not db.session.query(CrossrefTemp).filter_by(issn=issn).one_or_none():
            c = CrossrefTemp(issn=issn)
            db.session.add(c)
            db.session.flush()
    db.session.commit()
    sql = """
    delete from issn_temp
        where not exists (
            select null
            from crossref_temp
            where issn_temp.issn = crossref_temp.issn
    )
    """
    db.session.execute(sql)
    db.session.commit()


@app.cli.command("import_issn_apis")
def import_issn_apis():
    """
    Iterate over issn_metadata table, then fetch and store API data from issn.org and crossref.
    Save title and publisher to journals table.
    """
    i = 0
    while True:
        i += 100
        chunk = (
            ISSNMetaData.query.filter_by(updated_at=None)
            .order_by(func.random())
            .limit(100)
            .all()
        )
        if not chunk:
            break
        for issn in chunk:
            save_issn_org_api(issn)
            save_crossref_api(issn)
            set_title(issn)
            set_publisher(issn)
            link_issn_l(issn)

        if i % 10000 == 0:
            print("Chunk finished, number of ISSNs completed: ", i)
        db.session.commit()


def save_issn_org_api(issn):
    issn_org_url = "https://portal.issn.org/resource/ISSN/{}?format=json".format(
        issn.issn_l
    )
    try:
        r = requests.get(issn_org_url)
        if r.status_code == 200 and "@graph" in r.json():
            issn.issn_org_raw_api = r.json()
            issn.updated_at = datetime.datetime.now()
            db.session.commit()
    except (requests.exceptions.ConnectionError, json.JSONDecodeError):
        return


def save_crossref_api(issn):
    crossref_url = "https://api.crossref.org/journals/{}".format(issn.issn_l)
    try:
        r = requests.get(crossref_url)
        if r.status_code == 200 and ISSNMetaData.issn_org_raw_api:
            issn.crossref_raw_api = r.json()
            issn.updated_at = datetime.datetime.now()
            issn.crossref_issns = issn.issns_from_crossref_api
            db.session.commit()
    except requests.exceptions.ConnectionError:
        return None


def set_title(issn):
    try:
        j = Journal.query.filter_by(issn_l=issn.issn_l).one_or_none()
        title = remove_control_characters(issn.title_from_issn_api)
        if title and title[-1] == ".":
            title = title[:-1]
        if j and title and not j.is_modified_title:
            # update
            j.title = title
        elif title:
            j = Journal(issn_l=issn.issn_l, title=title)
            db.session.add(j)
            db.session.commit()
    except exc.IntegrityError:
        db.session.rollback()
        return


def set_publisher(issn):
    try:
        publisher = (
            get_or_create(db.session, Publisher, name=issn.publisher.strip('"'))
            if issn.publisher
            else None
        )
        j = Journal.query.filter_by(issn_l=issn.issn_l).one_or_none()
        if j:
            j.publisher_id = publisher.id if publisher else None
        db.session.commit()
    except exc.IntegrityError:
        db.session.rollback()
        return


def link_issn_l(issn):
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


@app.cli.command("set_publishers")
def set_publishers():
    """
    Iterate over issn_metadata table and set the publishers in the journals table.
    """
    for issn in ISSNMetaData.query.yield_per(100):
        publisher = (
            get_or_create(db.session, Publisher, name=issn.publisher)
            if issn.publisher
            else None
        )
        j = Journal.query.filter_by(issn_l=issn.issn_l).one_or_none()
        if j:
            j.publisher_id = publisher.id if publisher else None
    db.session.commit()

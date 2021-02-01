import datetime
from io import BytesIO
import json
from urllib.request import urlopen
from zipfile import ZipFile

import click
import requests
from sqlalchemy import func

from app import app, db
from models.issn import ISSNHistory, ISSNMetaData, ISSNTemp, ISSNToISSNL, LinkedISSNL
from models.journal import Journal, Publisher
from ingest.utils import get_or_create, remove_control_characters


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
        map_issns_to_issnl()
        # finished, remove temp data
        clear_issn_temp_table()

    else:
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
    for removed in removed_records:
        r = ISSNToISSNL.query.filter_by(
            issn=removed.issn, issn_l=removed.issn_l
        ).one_or_none()
        db.session.delete(r)
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


@app.cli.command("import_issn_apis")
def import_issn_apis():
    """
    Iterate over issn_metadata table, then fetch and store API data from issn.org and crossref.
    """
    while True:
        chunk = ISSNMetaData.query.filter_by(updated_at=None).order_by(func.random()).limit(100).all()
        if not chunk:
            break
        for issn in chunk:
            save_issn_org_api(issn)
            save_crossref_api(issn)
            set_title(issn)
            set_publisher(issn)
            link_issn_l(issn)
        db.session.commit()


def save_issn_org_api(issn):
    issn_org_url = "https://portal.issn.org/resource/ISSN/{}?format=json".format(
        issn.issn_l
    )
    try:
        r = requests.get(issn_org_url)
    except requests.exceptions.ConnectionError:
        return
    if r.status_code == 200:
        issn.issn_org_raw_api = r.json()
        issn.updated_at = datetime.datetime.now()
        db.session.commit()


def save_crossref_api(issn):
    crossref_url = "https://api.crossref.org/journals/{}".format(issn.issn_l)
    try:
        r = requests.get(crossref_url)
    except requests.exceptions.ConnectionError:
        return
    if r.status_code == 200:
        issn.crossref_raw_api = r.json()
        issn.updated_at = datetime.datetime.now()
        issn.crossref_issns = issn.issns_from_crossref_api
        db.session.commit()


def set_title(issn):
    j = Journal.query.filter_by(issn_l=issn.issn_l).one_or_none()
    title = remove_control_characters(issn.title_from_issn_api)
    if j:
        # update
        j.title = title
    else:
        j = Journal(issn_l=issn.issn_l, title=title)
        db.session.add(j)


def set_publisher(issn):
    publisher = (
        get_or_create(db.session, Publisher, name=issn.publisher)
        if issn.publisher
        else None
    )
    j = Journal.query.filter_by(issn_l=issn.issn_l).one_or_none()
    if j:
        j.publisher_id = publisher.id if publisher else None


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

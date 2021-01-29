import datetime
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import click
import requests

from app import app, db
from models.issn import ISSNToISSNL, ISSNTemp, ISSNHistory, ISSNMetaData


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
    issn_file = get_zipfile(zip_url) if not file_path else file_path

    # ensure temp ISSN table is empty
    db.session.query(ISSNTemp).delete()
    db.session.commit()

    # copy issn records into temp table
    copy_sql = "COPY issn_temp FROM STDOUT WITH (FORMAT CSV, DELIMITER '\t', HEADER)"
    conn = db.engine.raw_connection()
    with conn.cursor() as cur:
        if not file_path:
            cur.copy_expert(copy_sql, issn_file)
        else:
            with open(file_path, "rb") as f:
                cur.copy_expert(copy_sql, f)
    conn.commit()

    # sanity check
    if not file_path and ISSNTemp.query.count() < 2000000:
        print("not enough records in file")
        db.session.query(ISSNTemp).delete()
        db.session.commit()
        return

    # if initial load, simply copy the rows to the master table and map the issns
    if initial_load:
        db.session.execute(
            "INSERT INTO issn_to_issnl (issn, issn_l, created_at) SELECT issn, issn_l, NOW() FROM issn_temp;"
        )
        map_issns_to_issnl()
        # finished, remove temp data
        db.session.query(ISSNTemp).delete()
        db.session.commit()
        return

    # compare the regular ISSNtoISSNL table
    # new ISSN records (in temp but not in ISSNtoISSNL)
    new_records = db.session.execute(
        "SELECT issn, issn_l FROM issn_temp EXCEPT SELECT issn, issn_l FROM issn_to_issnl;"
    )

    # save new records
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

    # removed records (in ISSNtoISSNL but not in issn_temp)
    removed_records = db.session.execute(
        "SELECT issn, issn_l FROM issn_to_issnl EXCEPT SELECT issn, issn_l FROM issn_temp;"
    )
    for removed in removed_records:
        r = ISSNToISSNL.query.filter_by(
            issn=removed.issn, issn_l=removed.issn_l
        ).one_or_none()
        db.session.delete(r)
        db.session.add(
            ISSNHistory(issn_l=removed.issn_l, issn=removed.issn, status="removed")
        )
    db.session.commit()

    map_issns_to_issnl()

    # finished, remove temp data
    db.session.query(ISSNTemp).delete()
    db.session.commit()


def get_zipfile(zip_url):
    """
    Gets the remote CSV file.
    """
    resp = urlopen(zip_url)
    zipfile = ZipFile(BytesIO(resp.read()))
    file_name = find_file_name(zipfile)
    issn_file = zipfile.open(file_name)
    return issn_file


def find_file_name(zipfile):
    """
    Finds file from the zip archive ending with issn-to-issn-l.txt.
    """
    files = zipfile.namelist()
    select_file = [f for f in files if f.lower().endswith("issn-to-issn-l.txt")]
    file = select_file[0] if select_file else None
    return file


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
    issns = ISSNMetaData.query.all()
    for issn in issns:
        # issn.org api
        issn_org_url = "https://portal.issn.org/resource/ISSN/{}?format=json".format(
            issn.issn_l
        )
        i = requests.get(issn_org_url)
        if i.status_code == 200:
            issn.issn_org_raw_api = i.json()
            issn.updated_at = datetime.datetime.now()

        # crossref api
        crossref_url = "https://api.crossref.org/journals/{}".format(issn.issn_l)
        c = requests.get(crossref_url)
        if c.status_code == 200:
            issn.crossref_raw_api = c.json()
            issn.updated_at = datetime.datetime.now()

        db.session.commit()

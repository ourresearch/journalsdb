from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import click

from app import app, db
from models.issn import ISSNToISSNL, ISSNMetaData, ISSNTemp


@app.cli.command("import_issns")
@click.option("--file_path")
def import_issns(file_path):
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
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    if not file_path:
        cursor.copy_expert(copy_sql, issn_file)
    else:
        with open(file_path, "rb") as f:
            cursor.copy_expert(copy_sql, f)
    connection.commit()

    # sanity check
    if not file_path and ISSNTemp.query.count() < 2000000:
        print("not enough records in file")
        db.session.query(ISSNTemp).delete()
        db.session.commit()

    # compare the regular ISSNtoISSNL table
    # new ISSN records (in temp but not in ISSNtoISSNL)
    new_records = db.session.execute(
        "SELECT issn_l, issn FROM issn_temp EXCEPT SELECT issn_l, issn FROM issn_to_issnl;"
    )
    for new in new_records:
        db.session.add(ISSNToISSNL(issn_l=new.issn_l, issn=new.issn))
    db.session.commit()

    # removed records (in ISSNtoISSNL but not in issn_temp)
    removed_records = db.session.execute(
        "SELECT issn_l, issn FROM issn_to_issnl EXCEPT SELECT issn_l, issn FROM issn_temp;"
    )
    for removed in removed_records:
        r = ISSNToISSNL.query.filter_by(
            issn_l=removed.issn_l, issn=removed.issn
        ).one_or_none()
        db.session.delete(r)
    db.session.commit()

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


@app.cli.command("import_issn_mappings")
def import_issn_mappings():
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

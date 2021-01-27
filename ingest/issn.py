from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import click
import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from app import app, db
from models.issn import ISSNToISSNL


@app.cli.command("import_issns")
@click.option('--file_path')
def import_issns(file_path):
    """
    Master ISSN list: https://www.issn.org/wp-content/uploads/2014/03/issnltables.zip
    Available via a text file within the zip archive with name ISSN-to-ISSN-L-initial.txt.

    Read the issn-l to issn mapping from issn.org and save it to a table for further processing.

    Run with: flask import_issns
    """
    zip_url = "https://www.issn.org/wp-content/uploads/2014/03/issnltables.zip"
    issn_file = get_zipfile(zip_url) if not file_path else file_path

    cols = ["issn", "issn_l"]
    for chunk in pd.read_table(
        issn_file,
        chunksize=10000,
        header=None,
        keep_default_na=False,
        names=cols,
        skiprows=1,
    ):
        for row in chunk.to_dict(orient="records"):
            statement = (
                insert(ISSNToISSNL)
                .values(**row)
                .on_conflict_do_nothing(index_elements=["issn_l", "issn"])
            )
            db.session.execute(statement)
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


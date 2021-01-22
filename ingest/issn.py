import json
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd

from app import app, db


@app.cli.command("import_issns")
def import_issns():
    """
    Master ISSN list: https://www.issn.org/wp-content/uploads/2014/03/issnltables.zip
    Available via a text file within the zip archive with name 20210121.ISSN-L-to-ISSN.txt.
    issn-l: list of issns

    Run with: flask import_issns
    """
    zip_url = "https://www.issn.org/wp-content/uploads/2014/03/issnltables.zip"
    issn_file = get_zipfile(zip_url)

    cols = ['issn_l', 'issn_0', 'issn_1', 'issn_2', 'issn_3', 'issn_4']
    df = pd.read_table(issn_file, header=None, names=cols, skiprows=1, keep_default_na=False)

    # combine issns into list
    cols.remove('issn_l')
    df['issns'] = df[cols].values.tolist()

    # make new dataframe consisting of issn-l and list of issns
    new_df = df[['issn_l', 'issns']].copy()

    # clean issns list to remove empty strings
    new_df['issns'] = new_df['issns'].apply(lambda x: list(filter(None, x)))
    # new_df['issns'] = new_df['issns'].apply(lambda x: x.to_json(orient='values'))

    # save to database
    new_df.to_sql('raw_issn_org_data', con=db.engine, if_exists='append', index=False)


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
    Finds file from the zip archive ending with issn-l-to-issn.txt.
    """
    files = zipfile.namelist()
    select_file = [f for f in files if f.lower().endswith("issn-l-to-issn.txt")]
    file = select_file[0] if select_file else None
    return file

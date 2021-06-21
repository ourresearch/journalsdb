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
from ingest.utils import get_or_create, remove_control_characters
from models.issn import (
    ISSNHistory,
    ISSNMetaData,
    ISSNTemp,
    ISSNToISSNL,
    LinkedISSNL,
    MissingJournal,
)
from models.journal import Journal, Publisher


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
    issn_tsv_file = get_zipfile(zip_url) if not file_path else file_path

    # ensure temp ISSN temp table is empty
    clear_issn_temp_table()

    # copy issn records into temp table
    copy_tsv_to_temp_table(file_path, issn_tsv_file)

    # sanity check
    if not file_path and ISSNTemp.query.count() < 2000000:
        print("not enough records in file")
        clear_issn_temp_table()
        return

    # add crossref labels to temp table
    process_crossref_issns()

    # get new records in temp table
    print("run new records query")
    new_records = db.session.execute(
        "SELECT issn, issn_l, has_crossref FROM issn_temp t WHERE t.has_crossref is True AND NOT EXISTS (SELECT 1 FROM issn_to_issnl i where i.issn=t.issn and i.issn_l=t.issn_l);"
    )
    save_new_records(new_records)
    map_issns_to_issnl()
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
    print("load temp table")
    copy_sql = "COPY issn_temp(issn, issn_l) FROM STDOUT WITH (FORMAT CSV, DELIMITER '\t', HEADER)"
    conn = db.engine.raw_connection()
    with conn.cursor() as cur:
        if not file_path:
            cur.copy_expert(copy_sql, issn_file)
        else:
            # used with test files
            with open(file_path, "rb") as f:
                cur.copy_expert(copy_sql, f)
    conn.commit()
    print("load temp table complete")


def process_crossref_issns():
    """
    Iterate through crossref ISSNs coming from unpaywall, and add has_crossref True if the ISSN is in the issn.org list.
    If the ISSN is not in the issn.org list, then add it to the temp table.
    """
    print("adding crossref label")
    file = urlopen("https://api.unpaywall.org/crossref_issns.csv.gz")
    data = pd.read_csv(file, compression="gzip")

    crossref_issns = data["issn"].tolist()
    missing_journals = (
        db.session.query(MissingJournal)
        .filter_by(status="process", processed=False)
        .all()
    )
    missing_issns = [j.issn for j in missing_journals]
    mark_missing_journals_as_processed(missing_journals)
    issns_to_process = crossref_issns + missing_issns

    for issn in issns_to_process:
        r = db.session.query(ISSNTemp).filter_by(issn=issn).one_or_none()
        if r:
            issns_to_set = db.session.query(ISSNTemp).filter_by(issn_l=r.issn_l).all()
            for item in issns_to_set:
                item.has_crossref = True
        else:
            issn_exists = (
                db.session.query(ISSNToISSNL).filter_by(issn=issn).one_or_none()
            )
            if not issn_exists:
                save_issn_not_in_issn_org(issn)
        db.session.commit()
    print("adding crossref label complete")


def get_crossref_api_issns(issn):
    crossref_url = "https://api.crossref.org/journals/{}".format(issn)
    r = requests.get(crossref_url)

    result = {}
    try:
        if r.status_code == 200:
            result["issns"] = r.json()["message"]["ISSN"]
            result["issn_types"] = r.json()["message"]["issn-type"]

            for issn in result["issn_types"]:
                if issn["type"] == "electronic":
                    result["electronic_issn"] = issn["value"]
                elif issn["type"] == "print":
                    result["print_issn"] = issn["value"]
            return result
    except (requests.exceptions.ConnectionError, json.JSONDecodeError):
        return None


def save_issn_not_in_issn_org(issn):
    crossref_api_issns = get_crossref_api_issns(issn)

    if crossref_api_issns:
        # single issn pair, simply save to temp table
        if len(crossref_api_issns["issns"]) == 1:
            new_record = ISSNTemp(issn_l=issn, issn=issn, has_crossref=True)
            db.session.add(new_record)
            db.session.commit()
            print(
                "adding single record {} that is in crossref list but not in issn org".format(
                    issn
                )
            )

        # possible related issn
        elif len(crossref_api_issns["issns"]) == 2:
            related_issn = crossref_api_issns["issns"]
            related_issn.remove(issn)
            related_issn = related_issn[0]

            # check for existing record
            r = db.session.query(ISSNToISSNL).filter_by(issn=related_issn).one_or_none()
            if r:
                # add new issn but use the related record as the issn_l
                new_record = ISSNTemp(issn_l=r.issn_l, issn=issn, has_crossref=True)
                db.session.add(new_record)
                db.session.commit()
                print(
                    "adding {} but using related issn {} as the issn_l".format(
                        issn, r.issn_l
                    )
                )
            else:
                # add both records and use first record (electronic) as the issn_l
                if (
                    "electronic_issn" in crossref_api_issns
                    and "print_issn" in crossref_api_issns
                ):
                    try:
                        issn_exists = (
                            db.session.query(ISSNTemp)
                            .filter_by(issn=crossref_api_issns["electronic_issn"])
                            .one_or_none()
                        )
                        if issn_exists:
                            return
                        new_record_1 = ISSNTemp(
                            issn_l=crossref_api_issns["electronic_issn"],
                            issn=crossref_api_issns["electronic_issn"],
                            has_crossref=True,
                        )
                        db.session.add(new_record_1)
                        db.session.commit()
                    except exc.IntegrityError:
                        db.session.rollback()
                        print("duplicate record")

                    try:
                        issn_exists = (
                            db.session.query(ISSNTemp)
                            .filter_by(issn=crossref_api_issns["print_issn"])
                            .one_or_none()
                        )
                        if issn_exists:
                            return
                        new_record_2 = ISSNTemp(
                            issn_l=crossref_api_issns["electronic_issn"],
                            issn=crossref_api_issns["print_issn"],
                            has_crossref=True,
                        )
                        db.session.add(new_record_2)
                        db.session.commit()
                        print(
                            "adding {} and {} as electronic and print ISSNs".format(
                                crossref_api_issns["electronic_issn"],
                                crossref_api_issns["print_issn"],
                            )
                        )
                    except exc.IntegrityError:
                        db.session.rollback()
                        print("duplicate record")
        else:
            print("more than 2 records found!")


def save_new_records(new_records):
    print("save new records in issn_to_issnl table")
    objects = []
    history = []
    for new in new_records:
        objects.append(ISSNToISSNL(issn=new.issn, issn_l=new.issn_l))
        history.append(ISSNHistory(issn=new.issn, issn_l=new.issn_l, status="added"))
    db.session.bulk_save_objects(objects)
    db.session.bulk_save_objects(history)
    db.session.commit()
    print("save new records in issn_to_issnl table complete")


def map_issns_to_issnl():
    """
    Map issn-l to issns that are in the issn_to_issnl table.
    """
    print("map issns in metadata table")
    sql = """
    insert into issn_metadata (issn_l, issn_org_issns) (
        select
            issn_l,
            jsonb_agg(to_jsonb(issn)) as issn_org_issns
        from issn_to_issnl
        where issn_l is not null
        group by issn_l
    ) on conflict (issn_l) do update
    set issn_org_issns = excluded.issn_org_issns;
    """
    db.session.execute(sql)
    db.session.commit()
    print("map issns in metadata table complete")


def mark_missing_journals_as_processed(missing_journals):
    for j in missing_journals:
        j.processed = True
    db.session.commit()


@app.cli.command("import_issn_apis")
def import_issn_apis():
    """
    Iterate over issn_metadata table, then fetch and store API data from issn.org and crossref.
    Save title and publisher to journals table.
    """
    issns = ISSNMetaData.query.filter_by(updated_at=None).all()

    for issn in issns:
        save_issn_org_api(issn)
        save_crossref_api(issn)
        save_journal_with_title(issn)
        set_publisher(issn)
        link_issn_l(issn)

        # set updated_at
        issn.updated_at = datetime.datetime.now()
        db.session.commit()


def save_issn_org_api(issn):
    issn_org_url = "https://portal.issn.org/resource/ISSN/{}?format=json".format(
        issn.issn_l
    )
    try:
        r = requests.get(issn_org_url)
        if r.status_code == 200 and "@graph" in r.json():
            issn.issn_org_raw_api = r.json()
            db.session.commit()
            print("saving issn org data for issn {}".format(issn.issn_l))
        else:
            print("no issn org data found for {}".format(issn.issn_l))
    except (requests.exceptions.ConnectionError, json.JSONDecodeError):
        return


def save_crossref_api(issn):
    crossref_url = "https://api.crossref.org/journals/{}".format(issn.issn_l)
    try:
        r = requests.get(crossref_url)
        if r.status_code == 200:
            issn.crossref_raw_api = r.json()
            issn.crossref_issns = issn.issns_from_crossref_api
            db.session.commit()
            print("saving crossref data for issn {}".format(issn.issn_l))
        else:
            print("no crossref data for issn {}".format(issn.issn_l))
    except requests.exceptions.ConnectionError:
        return None


def save_journal_with_title(issn):
    try:
        j = Journal.query.filter_by(issn_l=issn.issn_l).one_or_none()
        title = remove_control_characters(issn.title_from_issn_api)
        if title and title[-1] == ".":
            title = title[:-1]
        if j and title and not j.is_modified_title:
            # update
            j.title = title
            print("setting journal title to {}".format(title))
        elif title:
            j = Journal(issn_l=issn.issn_l, title=title)
            db.session.add(j)
            db.session.commit()
            print(
                "added new journal with issn_l {} and title {}".format(
                    issn.issn_l, title
                )
            )
    except exc.IntegrityError:
        db.session.rollback()
        return


def set_publisher(issn):
    try:
        publisher = (
            get_or_create(db.session, Publisher, name=issn.publisher)
            if issn.publisher
            else None
        )
        j = Journal.query.filter_by(issn_l=issn.issn_l).one_or_none()
        if j and publisher:
            j.publisher_id = publisher.id
            print("setting journal {} with publisher {}".format(j.issn_l, publisher))
        db.session.commit()
    except exc.IntegrityError:
        db.session.rollback()
        return


def link_issn_l(issn):
    try:
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
    except exc.IntegrityError:
        db.session.rollback()
        return


@app.cli.command("move_issn")
@click.option("--issn_from", prompt=True)
@click.option("--issn_to", prompt=True)
def move_issn(issn_from, issn_to):
    # delete journal entry
    j = db.session.query(Journal).filter_by(issn_l=issn_from).one_or_none()
    if j:
        db.session.delete(j)
        db.session.commit()
        print("journal entry for issn {} deleted".format(issn_from))
    else:
        # journal may have been mapped to different issn_l
        r = db.session.query(ISSNToISSNL).filter_by(issn=issn_from).first()
        if r and r.issn_l != issn_to:
            issn_l = r.issn_l
            j = db.session.query(Journal).filter_by(issn_l=issn_l).one()
            db.session.delete(j)
            db.session.commit()
            print("journal entry deleted using mapped issn_l {}".format(issn_l))

    # delete issn_metadata entry
    i = db.session.query(ISSNMetaData).filter_by(issn_l=issn_from).one_or_none()
    if i:
        db.session.delete(i)
        db.session.commit()
        print("issn metadata for issn {} deleted".format(issn_from))
    else:
        # metadata may have been mapped to different issn_l
        r = db.session.query(ISSNToISSNL).filter_by(issn=issn_from).first()
        if r and r.issn_l != issn_to:
            issn_l = r.issn_l
            i = db.session.query(ISSNMetaData).filter_by(issn_l=issn_l).one()
            db.session.delete(i)
            db.session.commit()
            print("issn metadata deleted using mapped issn_l {}".format(issn_l))

    # delete from issn_to_issnl
    issn_to_remove = db.session.query(ISSNToISSNL).filter_by(issn=issn_from).first()
    if issn_to_remove:
        mapped_issns = (
            db.session.query(ISSNToISSNL).filter_by(issn_l=issn_to_remove.issn_l).all()
        )
        for issn in mapped_issns:
            db.session.delete(issn)
            db.session.commit()
            print(
                "issn to issnl mapping data for issn {} and issn_l {} deleted".format(
                    issn.issn, issn.issn_l
                )
            )

    # add to issn_to_issnl with new issn_l
    issn_to_issnl = ISSNToISSNL(issn_l=issn_to, issn=issn_from)
    db.session.add(issn_to_issnl)
    db.session.commit()
    print("issn {} mapped to {} in issn to issnl table".format(issn_from, issn_to))

    # add issn to issn_org_issns in issn_metadata
    metadata = db.session.query(ISSNMetaData).filter_by(issn_l=issn_to).one()
    metadata.issn_org_issns = metadata.issn_org_issns + [issn_from]
    db.session.commit()
    print(
        "issn {} added to issn_org column for {} issn_l metadata record".format(
            issn_from, issn_to
        )
    )


@app.cli.command("add_from_worldcat")
@click.option("--issn", prompt=True)
@click.option("--journal_title", prompt=True)
@click.option("--publisher_id", prompt=True)
def add_from_worldcat(issn, journal_title, publisher_id):
    """
    Command used to manually add journals that are found in worldcat but nowhere else.
    """
    issn_to_issnl = ISSNToISSNL(issn_l=issn, issn=issn)
    db.session.add(issn_to_issnl)
    db.session.commit()
    print("issn {} mapped to {} in issn to issnl table".format(issn, issn))

    # add issn to issn_org_issns in issn_metadata
    metadata = ISSNMetaData(
        issn_l=issn, issn_org_issns=[issn], updated_at=datetime.datetime.now()
    )
    db.session.add(metadata)
    db.session.commit()
    print(
        "issn {} added to issn_org column for {} issn_l metadata record".format(
            issn, issn
        )
    )

    j = Journal(issn_l=issn, title=journal_title, publisher_id=int(publisher_id))
    db.session.add(j)
    db.session.commit()
    print("journal saved {} {} {}".format(issn, journal_title, int(publisher_id)))

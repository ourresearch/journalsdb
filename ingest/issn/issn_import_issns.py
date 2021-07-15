from io import BytesIO
import json
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd
import requests
from sqlalchemy import exc

from app import db
from models.issn import (
    ISSNHistory,
    ISSNTemp,
    ISSNToISSNL,
    MissingJournal,
)


crossref_issns_url = "https://api.unpaywall.org/crossref_issns.csv.gz"
issn_org_zip_url = "https://www.issn.org/wp-content/uploads/2014/03/issnltables.zip"


def import_issns():
    """
    Core function that imports the ISSNs.
    """
    issn_tsv_file = get_zipfile()

    # ensure ISSN temp table is empty
    clear_issn_temp_table()

    # copy issn records into temp table
    copy_tsv_to_temp_table(issn_tsv_file)

    # sanity check
    if ISSNTemp.query.count() < 2000000:
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


def get_zipfile():
    """
    Fetches the remote zip file.
    """
    resp = urlopen(issn_org_zip_url)
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


def copy_tsv_to_temp_table(issn_file):
    """
    Very fast way to copy 1 million or more rows into a table.
    """
    print("load temp table")
    copy_sql = "COPY issn_temp(issn, issn_l) FROM STDOUT WITH (FORMAT CSV, DELIMITER '\t', HEADER)"
    conn = db.engine.raw_connection()
    with conn.cursor() as cur:
        cur.copy_expert(copy_sql, issn_file)
    conn.commit()
    print("load temp table complete")


def process_crossref_issns():
    """
    Iterate through crossref ISSNs coming from unpaywall, and add has_crossref True if the ISSN is in the issn.org list.
    If the ISSN is not in the issn.org list, then add it to the temp table.
    """
    print("adding crossref label")
    file = urlopen(crossref_issns_url)
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

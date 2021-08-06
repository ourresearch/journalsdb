from io import BytesIO
import json
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd
import requests

from app import db
from ingest.issn.issn_exceptions import InsufficientRecords
from models.issn import (
    ISSNHistory,
    ISSNTemp,
    ISSNToISSNL,
    MissingJournal,
)


UNPAYWALL_ISSNS_URL = "https://api.unpaywall.org/crossref_issns.csv.gz"
ISSN_ORG_ZIP_URL = "https://www.issn.org/wp-content/uploads/2014/03/issnltables.zip"


def import_issns():
    """
    Core function that imports the ISSNs. End result is to add ISSNs to the issn_to_issnl table, that are then mapped as
    issn_l -> issns in the issn_metadata table. The issn_to_issnl table is kept safe by this function only adding issns
    (not deleting). The issn column is set to unique, so if an issn already exists an error will occur.
    """
    copy_issn_org_issns_into_temp_table()

    # mark the issns we want to keep
    mark_issns_to_keep()

    # get new records in temp table
    print("run new records query")
    new_records = db.session.execute(
        """
        SELECT issn, issn_l, has_crossref
        FROM issn_temp t
        WHERE t.has_crossref is True
            AND NOT EXISTS(SELECT 1 FROM issn_to_issnl i where i.issn = t.issn and i.issn_l = t.issn_l);
        """
    )
    save_new_records(new_records)
    map_issns_to_issnl()

    # cleanup
    missing_journals = get_missing_journals()
    mark_missing_journals_as_processed(missing_journals)
    clear_issn_temp_table()


def copy_issn_org_issns_into_temp_table():
    issn_org_tsv_file = get_zipfile()

    # ensure ISSN temp table is empty
    clear_issn_temp_table()

    # copy issn records into temp table
    copy_tsv_to_temp_table(issn_org_tsv_file)

    # sanity check
    if ISSNTemp.query.count() < 2000000:
        print("not enough records in file")
        clear_issn_temp_table()
        raise InsufficientRecords("Not enough records in dataset")


def get_zipfile():
    """
    Fetches the remote zip file.
    """
    resp = urlopen(ISSN_ORG_ZIP_URL)
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


def clear_issn_temp_table():
    db.session.query(ISSNTemp).delete()
    db.session.commit()


def copy_tsv_to_temp_table(issn_file):
    """
    Copies the records from the issn.org tsv file into the issn_temp table.
    """
    print("load temp table")
    copy_sql = "COPY issn_temp(issn, issn_l) FROM STDOUT WITH (FORMAT CSV, DELIMITER '\t', HEADER)"
    conn = db.engine.raw_connection()
    with conn.cursor() as cur:
        cur.copy_expert(copy_sql, issn_file)
    conn.commit()
    print("load temp table complete")


def mark_issns_to_keep():
    """
    Iterate through crossref ISSNs coming from unpaywall, and add has_crossref True if the ISSN is in the issn.org list.
    If the ISSN is not in the issn.org list, then add it to the temp table.
    """
    print("marking issns we want to keep (with has_crossref label)")
    issns_to_keep = get_issns_to_keep()
    # mark_missing_journals_as_processed(missing_journals)

    for issn in issns_to_keep:
        mark_to_keep(issn)
    print("marking issns complete.")


def get_issns_to_keep():
    unpaywall_issns = get_unpaywall_issns()
    missing_issns = get_missing_issns()
    issns_to_keep = unpaywall_issns + missing_issns
    return issns_to_keep


def get_unpaywall_issns():
    file = urlopen(UNPAYWALL_ISSNS_URL)
    data = pd.read_csv(file, compression="gzip")
    unpaywall_issns = data["issn"].tolist()
    return unpaywall_issns


def get_missing_issns():
    """
    List of ISSNs that were identified as missing based on the missing_journal endpoint.
    """
    missing_journals = get_missing_journals()
    missing_issns = [j.issn for j in missing_journals]
    return missing_issns


def get_missing_journals():
    """
    Journal records that were submitted as 'missing' via the missing_journal endpoint.
    """
    missing_journals = (
        db.session.query(MissingJournal)
        .filter_by(status="process", processed=False)
        .all()
    )
    return missing_journals


def mark_to_keep(issn):
    r = db.session.query(ISSNTemp).filter_by(issn=issn).one_or_none()
    if r:
        issns_to_set = db.session.query(ISSNTemp).filter_by(issn_l=r.issn_l).all()
        for item in issns_to_set:
            item.has_crossref = True
    else:
        issn_exists = db.session.query(ISSNToISSNL).filter_by(issn=issn).one_or_none()
        if not issn_exists:
            # issn is not in the normal issn.org mapping, so we need to handle it differently
            process_issn_not_in_issn_org(issn)
    db.session.commit()


def process_issn_not_in_issn_org(issn):
    """
    The issn is not in the standard issn.org mapping, so we are going to check to see if it is in
    crossref via https://api.crossref.org/journals/<issn>.
    """
    crossref_api_issns = get_crossref_api_issns(issn)

    # single issn, simply save to temp table
    if len(crossref_api_issns["issns"]) == 1:
        save_single_issn_from_crossref(issn)

    # possible related issn
    elif len(crossref_api_issns["issns"]) == 2:
        related_issn = crossref_api_issns["issns"]
        related_issn.remove(issn)  # remove the issn we already have
        related_issn = related_issn[0]

        # check for existing record
        related_record = (
            db.session.query(ISSNToISSNL).filter_by(issn=related_issn).one_or_none()
        )
        if related_record:
            save_issn_using_related_issnl(issn, related_record)
        else:
            # add both records and use first record (electronic) as the issn_l
            save_both_issns_from_crossref(crossref_api_issns)
    elif len(crossref_api_issns["issns"]) > 2:
        # don't do anything if there are more than two issns
        print(
            "more than 2 records found for issn {}, crossref_api_issns {}".format(
                issn, crossref_api_issns
            )
        )


def get_crossref_api_issns(issn):
    crossref_url = "https://api.crossref.org/journals/{}".format(issn)
    r = requests.get(crossref_url)

    result = {"issns": []}
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
        return result
    except (requests.exceptions.ConnectionError, json.JSONDecodeError):
        return result


def save_single_issn_from_crossref(issn):
    new_record = ISSNTemp(issn_l=issn, issn=issn, has_crossref=True)
    db.session.add(new_record)
    db.session.commit()
    print(
        "adding single record {} that is in crossref list but not in issn org".format(
            issn
        )
    )


def save_issn_using_related_issnl(issn, related):
    # add new issn but use the related record as the issn_l
    new_record = ISSNTemp(issn_l=related.issn_l, issn=issn, has_crossref=True)
    db.session.add(new_record)
    db.session.commit()
    print(
        "adding {} but using related issn {} as the issn_l".format(issn, related.issn_l)
    )


def save_both_issns_from_crossref(crossref_api_issns):
    if "electronic_issn" in crossref_api_issns and "print_issn" in crossref_api_issns:
        issn_exists_mapped = (
            db.session.query(ISSNToISSNL)
            .filter_by(issn=crossref_api_issns["electronic_issn"])
            .one_or_none()
        )
        issn_exists_temp = (
            db.session.query(ISSNTemp)
            .filter_by(issn=crossref_api_issns["electronic_issn"])
            .one_or_none()
        )
        if not issn_exists_mapped and not issn_exists_temp:
            new_record_1 = ISSNTemp(
                issn_l=crossref_api_issns["electronic_issn"],
                issn=crossref_api_issns["electronic_issn"],
                has_crossref=True,
            )
            db.session.add(new_record_1)
            db.session.commit()

        issn_exists_mapped = (
            db.session.query(ISSNToISSNL)
            .filter_by(issn=crossref_api_issns["print_issn"])
            .one_or_none()
        )
        issn_exists_temp = (
            db.session.query(ISSNTemp)
            .filter_by(issn=crossref_api_issns["print_issn"])
            .one_or_none()
        )
        if not issn_exists_mapped and not issn_exists_temp:
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


def save_new_records(new_records):
    print("save new records in issn_to_issnl table")
    issns_to_ignore = [
        "1931-3756",
        "2633-0032",
        "2057-0481",
        "2200-6974",
        "2633-5603",
        "1539-6053",
        "0971-7625",
        "0263-8762",
        "1744-3563",
        "2145-7166",
    ]  # sage issns that were merged together and conflict with issn.org list
    objects = []
    history = []
    for new in new_records:
        if new.issn not in issns_to_ignore:
            objects.append(ISSNToISSNL(issn=new.issn, issn_l=new.issn_l))
            history.append(
                ISSNHistory(issn=new.issn, issn_l=new.issn_l, status="added")
            )
    db.session.bulk_save_objects(objects)
    db.session.bulk_save_objects(history)
    db.session.commit()
    print("save new records in issn_to_issnl table complete")


def mark_missing_journals_as_processed(missing_journals):
    for j in missing_journals:
        j.processed = True
    db.session.commit()


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

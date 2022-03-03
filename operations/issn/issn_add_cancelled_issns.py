from json.decoder import JSONDecodeError

import pandas as pd
import re
import requests

from app import db
from models.issn import ISSNMetaData, ISSNToISSNL


def add_cancelled_issns():
    df = pd.read_csv("operations/issn/issn_with_status.csv")

    for index, row in df.iterrows():
        if row.status == 404:
            r = requests.get(
                f"https://portal.issn.org/resource/ISSN/{row.issn}?format=json"
            )
            try:
                if r.status_code == 200:
                    response = r.json()
                    if "@graph" in response:
                        for item in response["@graph"]:
                            if "cancelledInFavorOf" in item:
                                issn_path = item["cancelledInFavorOf"]
                                if type(issn_path) == list:
                                    issn_path = issn_path[0]
                                existing_issn = extract_issn(issn_path)
                                map_new_issn_to_old_issn(row.issn, existing_issn)
                                print(row.issn, existing_issn)
            except JSONDecodeError:
                continue


def extract_issn(path):
    issn_match = re.search("\d{4}-\d{4}", path)
    return issn_match.group()


def map_new_issn_to_old_issn(new_issn, existing_issn):
    # check if issn_l exists
    issn_to = ISSNToISSNL.query.filter_by(issn=existing_issn).first()
    issn_already_exsists = ISSNToISSNL.query.filter_by(issn=new_issn).first()
    if issn_to and not issn_already_exsists:
        issn_to_issnl = ISSNToISSNL(issn_l=issn_to.issn_l, issn=new_issn)
        db.session.add(issn_to_issnl)

        metadata = db.session.query(ISSNMetaData).filter_by(issn_l=issn_to.issn_l).one()
        metadata.issn_org_issns = metadata.issn_org_issns + [new_issn]
        print(
            "issn {} added to issn_org column for {} issn_l metadata record".format(
                new_issn, issn_to.issn_l
            )
        )
        db.session.commit()

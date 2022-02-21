import time

import requests

from app import app, db
from models.usage import DOICount


@app.cli.command("import_sample_dois")
def import_sample_dois():
    records_to_update = (
        db.session.query(DOICount).filter(DOICount.sample_dois == None).all()
    )
    for row in records_to_update:
        url = "https://api.crossref.org/journals/{}/works?sample=3&mailto=team@ourresearch.org".format(
            row.issn_l
        )
        r = requests.get(url)

        if r.status_code != 200:
            # try other issn
            for issn in row.issns:
                if issn != row.issn_l:
                    url = "https://api.crossref.org/journals/{}/works?sample=3&mailto=team@ourresearch.org".format(
                        issn
                    )
                    r = requests.get(url)

        if r.status_code == 200:
            dois = []
            i = 0
            for article in r.json()["message"]["items"]:
                dois.append(article["DOI"])
                i = i + 1
                if i > 3:
                    break
            print("adding sample dois {} for issn_l {}".format(dois, row.issn_l))
            row.sample_dois = dois
            db.session.commit()
        time.sleep(0.01)

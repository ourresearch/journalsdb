import pandas as pd

from ingest.open_access import import_open_access
from models.usage import OpenAccessPublishing, OpenAccessStatus
from models.journal import Journal
from views import app


test_data = {
    "issn_l": ["1876-2859"],
    "title": ["Tropical Parasitology"],
    "year": ["2010"],
    "num_dois": ["10"],
    "num_open": [7],
    "open_rate": ["0.7"],
    "num_green": [7],
    "green_rate": ["0.7"],
    "num_bronze": [0],
    "bronze_rate": ["0.0"],
    "num_hybrid": [0],
    "hybrid_rate": ["0.0"],
    "num_gold": [0],
    "gold_rate": ["0.0"],
    "is_in_doaj": [False],
    "is_gold_journal": [False],
}


def test_import_open_access(client, run_import_issns_with_api, mocker):
    mocker.patch(
        "ingest.open_access.pd.read_csv",
        return_value=pd.DataFrame(data=test_data),
    )
    run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")

    # run command
    runner = app.test_cli_runner()
    runner.invoke(import_open_access)

    j = Journal.query.filter_by(issn_l="1876-2859").one()
    oas = OpenAccessStatus.query.filter_by(journal_id=j.id).one()

    assert oas.is_in_doaj is False
    assert oas.year == 2010

    oap = OpenAccessPublishing.query.filter_by(journal_id=j.id).one()
    assert oap.num_dois == 10
    assert oap.open_rate == 0.7

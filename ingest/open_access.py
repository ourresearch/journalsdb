from app import app
from ingest.utils import CSVImporter
from models.usage import OpenAccess


@app.cli.command("import_open_access")
def import_open_access():
    """
    Open access data: https://api.unpaywall.org/journal_open_access.csv.gz

    Counts the number of articles with each oa_status by (issn_l, year).
    num_open = num_green + num_bronze + num_hybrid + num_gold
    {status}_rate = num_{status} / num_dois

    issn_l (string, pkey)
    title (string, nullable)
    year (integer, pkey)
    num_dois (integer)
    num_open (integer)
    open_rate (double precision)
    num_green (integer)
    green_rate (double precision)
    num_bronze (integer)
    bronze_rate (double precision)
    num_hybrid (integer)
    hybrid_rate (double precision)
    num_gold (integer)
    gold_rate (double precision)
    is_in_doaj (boolean)
    is_gold_journal (boolean)

    Run with: flask import_open_access
    """
    url = "https://api.unpaywall.org/journal_open_access.csv.gz"

    # field setup
    fields = OpenAccess.__table__.columns.keys()
    fields_to_remove = ["id", "created_at", "updated_at"]
    for field in fields_to_remove:
        fields.remove(field)
    fields = ",".join(fields)

    # import TODO: need to ensure all fields are updated on update not just one
    c = CSVImporter(fields=fields, table="open_access", url=url)
    c.import_data()

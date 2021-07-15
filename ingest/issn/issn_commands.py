from app import app
from ingest.issn.issn_import_issns import import_issns


@app.cli.command("import_issns")
def import_issns_command():
    """
    Master ISSN list: https://www.issn.org/wp-content/uploads/2014/03/issnltables.zip
    Available via a text file within the zip archive with name ISSN-to-ISSN-L-initial.txt.

    Read the issn-l to issn mapping from issn.org and save it to a table for further processing.
    """
    import_issns()

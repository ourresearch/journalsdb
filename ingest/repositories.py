from app import app, db
from ingest.utils import CSVImporter
from models.usage import Repository


@app.cli.command("import_repositories")
def import_repositories():
    """
    Repository article counts: https://api.unpaywall.org/repositories.csv.gz

    issn_l (string, pkey)
    endpoint_id (string, pkey)
    repository_name  (string, nullable)
    institution_name (string, nullable)
    home_page (string, nullable)
    pmh_url (string, nullable)
    num_articles (integer)

    Run with: flask import_repositories
    """

    class RepositoryImporter(CSVImporter):
        def create_temp_table(self):
            db.session.execute(
                "CREATE TABLE {} ( like {} including all)".format(
                    self.staging_table, self.table
                )
            )
            db.session.commit()

        def copy_temp_to_standard(self):
            copy_sql = "INSERT INTO {table} ({fields}) SELECT {fields} FROM {staging_table} ON CONFLICT (issn_l, endpoint_id) DO UPDATE SET repository_name=excluded.repository_name;".format(
                table=self.table, fields=self.fields, staging_table=self.staging_table
            )
            db.session.execute(copy_sql)
            db.session.commit()

    fields = Repository.__table__.columns.keys()
    fields = ",".join(fields)
    importer = RepositoryImporter(
        fields=fields,
        table="repositories",
        url="https://api.unpaywall.org/repositories.csv.gz",
    )
    importer.import_data()

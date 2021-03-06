"""
Goal is to import journal pricing data from the top five academic journal publishers. So overall flow is:

1. Look up journal by ISSN (using method Journal.find_by_issn(issn))
2. Save subscription price with associated currency and region (USA, UK, rest of world, etc)
3. Save publisher's internal ID as internal_publisher_id in the journals table
4. Some journals are part of a package or 'mini bundle' so will need to be saved as a mini bundle.
"""
import os

import click

from app import app, db
from ingest.subscription.elsevier import Elsevier
from ingest.subscription.sage import Sage
from ingest.subscription.springer_nature import SpringerNature
from ingest.subscription.taylor_francis import TaylorFrancis
from ingest.subscription.wiley_blackwell import WileyBlackwell
from models.price import SubscriptionPrice
from models.journal import Journal

CSV_DIRECTORY = "ingest/subscription/files/"


@app.cli.command("import_wb")
@click.option("--file_name", default="wiley_sub_2021.xlsx")
@click.option("--year", required=True)
def import_wb(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    wb = WileyBlackwell(year)
    wb.format_wb_dataframe(file_path)
    wb.add_regions_to_db()
    wb.import_wiley_blackwell()


@app.cli.command("import_elsevier")
@click.option("--file_name", required=True)
@click.option("--year", required=True)
def import_elsevier(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    e = Elsevier(year)
    e.format_elsevier_dataframe(file_path)
    e.add_regions_to_db()
    e.import_elsevier_prices()


@app.cli.command("import_tf")
@click.option("--file_name", default="taylor_francis_sub_2021.xlsx")
@click.option("--year", required=True)
def import_tf(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    tf = TaylorFrancis(year)
    tf.format_tf_dataframe(file_path)
    tf.add_regions_to_db()
    tf.import_prices()


@app.cli.command("import_sage")
@click.option("--file_name", default="sage_sub_2021.xlsx")
@click.option("--year", required=True)
def import_sage(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    s = Sage(year)
    s.format_sage_dataframe(file_path)
    s.add_regions_to_db()
    s.import_prices()


@app.cli.command("import_springer")
@click.option("--file_name", default="springer_sub_2021.xlsx")
@click.option("--year", required=True)
def import_springer(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    s = SpringerNature(year)
    s.format_springer_dataframe(file_path)
    s.add_regions_to_db()
    s.import_prices()


@app.cli.command("delete_all_prices")
def delete_prices():
    db.session.query(Journal).update({Journal.subscription_prices: []})
    num_rows_deleted = db.session.query(SubscriptionPrice).delete()
    print("Deleted {} Prices".format(num_rows_deleted))
    db.session.commit()

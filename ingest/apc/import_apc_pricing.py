import os

import click

from app import app, db
from ingest.apc.apc_elsevier import ElsevierAPC
from ingest.apc.apc_wiley import WileyAPC
from ingest.apc.apc_springer import SpringerAPC
from ingest.apc.apc_sage import SageAPC
from models.journal import Journal
from models.price import APCPrice

CSV_DIRECTORY = "ingest/apc/files/"


@app.cli.command("import_apc_sage")
@click.option("--file_name", required=True)
@click.option("--year", required=True)
def import_sage(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    sage = SageAPC(year)
    sage.parse_excel(file_path)
    sage.import_prices()


@app.cli.command("import_apc_elsevier")
@click.option("--file_name", required=True)
@click.option("--year", required=True)
def import_elsevier(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    elsevier = ElsevierAPC(year)
    elsevier.parse_excel(file_path)
    elsevier.import_prices()


@app.cli.command("import_apc_wiley")
@click.option("--file_name", required=True)
@click.option("--is_hybrid", required=True)
@click.option("--year")
def import_wb(file_name, is_hybrid, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    wiley = WileyAPC(year)

    hybrid = False

    if is_hybrid.lower() == "true":
        hybrid = True

    if hybrid:
        # Import Hybrid Full Pricing
        wiley.parse_excel(file_path, is_hybrid=True)
        wiley.narrow_dataframe([0, 1, 2, 3, 4])
        wiley.import_prices()

    else:
        # Import Full Price Group
        wiley.parse_excel(file_path, is_hybrid=False)
        wiley.narrow_dataframe([0, 1, 2, 3, 4, 5, 15])
        wiley.import_prices()


@app.cli.command("import_apc_springer")
@click.option("--file_name", required=True)
@click.option("--is_hybrid", required=True)
@click.option("--year")
def import_springer(file_name, is_hybrid, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    springer = SpringerAPC(year)

    hybrid = False

    if is_hybrid.lower() == "true":
        hybrid = True

    if hybrid:
        springer.parse_excel(file_path, is_hybrid=True)
        springer.import_prices()

    else:
        springer.parse_excel(file_path, is_hybrid=False)
        springer.import_prices()


@app.cli.command("delete_apc_prices")
def delete_apc_prices():
    journals = db.session.query(Journal).all()
    for j in journals:
        j.apc_prices = []
    db.session.flush()
    apc_prices = db.session.query(APCPrice).all()
    for price in apc_prices:
        db.session.delete(price)
    db.session.commit()

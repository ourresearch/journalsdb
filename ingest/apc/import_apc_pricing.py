import os

import click

from app import app, db
from ingest.apc.apc_elsevier import ElsevierAPC
from models.journal import Journal
from models.price import APCPrice

CSV_DIRECTORY = "ingest/apc/files/"


@app.cli.command("import_apc_elsevier")
@click.option("--file_name", required=True)
@click.option("--year", required=True)
def import_wb(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    elsevier = ElsevierAPC(year)
    elsevier.parse_excel(file_path)
    elsevier.import_prices()


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

"""
Goal is to import journal pricing data from the top five academic journal publishers. So overall flow is:

1. Look up journal by ISSN (using method Journal.find_by_issn(issn))
2. Save subscription price with associated currency and region (USA, UK, rest of world, etc)
3. Save publisher's internal ID as internal_publisher_id in the journals table
4. Some journals are part of a package or 'mini bundle' so will need to be saved as a mini bundle.
"""
import os

import click
import pandas as pd

from app import app, db
from ingest.subscription.subscription_elsevier import Elsevier
from ingest.subscription.subscription_sage import Sage, SageMiniBundle
from ingest.subscription.subscription_springer import SpringerNature
from ingest.subscription.subscription_taylor import TaylorFrancis, TaylorMiniBundle
from ingest.subscription.subscription_wiley import WileyBlackwell
from models.journal import Journal
from models.price import Country, Currency, MiniBundle, Region, SubscriptionPrice
from ingest.utils import get_or_create

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


# mini bundles


@app.cli.command("import_mini_bundle")
@click.option("--file_name", default="mini_bundle.csv")
@click.option("--year", required=True)
def import_mini_bundle(file_name, year):
    df = pd.read_csv(CSV_DIRECTORY + file_name, keep_default_na=False)
    for index, row in df.iterrows():
        # get or save mini bundle
        mb = get_or_create(
            db.session, MiniBundle, name=row["name"], publisher_id=row["publisher_id"]
        )

        # create price if it does not exist
        currency = Currency.query.filter_by(acronym=row["currency"].upper()).one()
        country = Country.query.filter_by(iso3=row["country"].upper()).one_or_none()
        region = Region.query.filter_by(
            name=row["region"], publisher_id=int(row["publisher_id"])
        ).one_or_none()
        price_found = False
        for p in mb.subscription_prices:
            if (
                p.price == float(row["price"])
                and p.country == country
                and p.currency == currency
                and p.region == region
            ):
                print(
                    "Price exists for mini bundle {} with price {}".format(
                        row["name"], row["price"]
                    )
                )
                price_found = True

        if not price_found:
            new_price = SubscriptionPrice(
                price=float(row["price"]),
                country=country,
                currency=currency,
                region=region,
                year=year,
            )
            db.session.add(new_price)
            # match price to mini bundle
            mb.subscription_prices.append(new_price)
            print("Adding price {} to mini bundle {}".format(row["price"], row["name"]))
            db.session.commit()

        # assign journals to mini bundle
        issns = row["issns"].split(",")
        for issn in issns:
            j = Journal.find_by_issn(issn.strip())
            if j and j not in mb.journals:
                print(
                    "assigning journal with issn {} to mini bundle {}".format(
                        j.issn_l, row["name"]
                    )
                )
                mb.journals.append(j)
            elif j:
                print(
                    "Journal with issn {} already assigned to mini bundle {}".format(
                        j.issn_l, row["name"]
                    )
                )
            else:
                print("Journal does not exist for issn {}".format(issn))

        db.session.commit()


@app.cli.command("sage_mb")
@click.option("--file_name", default="sage_sub_2021.xlsx")
@click.option("--year", required=True)
def sage_mb(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    s = SageMiniBundle(year)
    s.format_sage_dataframe(file_path)
    s.import_prices()


@app.cli.command("taylor_mb")
@click.option("--file_name", default="taylor_francis_sub_2021.xlsx")
@click.option("--year", required=True)
def taylor_mb(file_name, year):
    file_path = os.path.join(app.root_path, CSV_DIRECTORY, file_name)
    t = TaylorMiniBundle(year)
    t.format_tf_dataframe(file_path)
    t.import_prices()

import os

import pandas as pd

from app import app, db
from models.location import Country, Continent


@app.cli.command("import_locations")
def import_locations():
    """
    Imports location data from a specified CSV file.
    CSV data pulled from https://datahub.io/JohnSnowLabs/country-and-continent-codes-list
    run with flask import_locations
    """
    csv_file = os.path.join(app.root_path, "ingest/files/locations.csv")
    df = pd.read_csv(csv_file, keep_default_na=False)

    continents_and_ids = {}

    for index, row in df.iterrows():
        continent = row["Continent_Name"]
        if continent in continents_and_ids.keys():
            continent_id = continents_and_ids[continent]
        else:
            continent_entry = Continent(name=continent)
            db.session.add(continent_entry)
            db.session.flush()
            continent_id = continent_entry.id
            continents_and_ids[continent] = continent_id
            print("Adding continent to database: ", continent)

        country = (
            db.session.query(Country.iso)
            .filter_by(iso=row["Two_Letter_Country_Code"])
            .scalar()
        )

        if not country:
            print("adding country", row["Country_Name"])
            country = Country(
                name=row["Country_Name"],
                iso=row["Two_Letter_Country_Code"],
                iso3=row["Three_Letter_Country_Code"],
                continent_id=continent_id,
            )
            db.session.add(country)
            db.session.flush()

    db.session.commit()

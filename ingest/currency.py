import os
import pandas as pd

from app import app, db
from models.price import Currency


@app.cli.command("import_currency")
def import_currency():
    """
    Loads up a provided CSV file of world currencies and extracts the unicode symbol
    and text label associated with each currency. Loads these into the Currency table
    in the price model.

    CSV to use: https://gist.github.com/Chintan7027/fc4708d8b5c8d1639a7c#file-currency-symbols-csv

    The Serbia Dinar has a '.' at the end which is removed by this script.
    INR value should be updated manually with the _unicode-decimal value 8377

    Run with 'flask import_currency'
    """
    csv_file = os.path.join(app.root_path, "ingest/files/currency.csv")
    df = pd.read_csv(csv_file)
    df = df.dropna()

    MAX_SYMBOL_LENGTH = 3

    for index, row in df.iterrows():
        unicode_decimal = str(row["_unicode-decimal"])
        unicode_as_array = unicode_decimal.split(", ")[:MAX_SYMBOL_LENGTH]
        symbol = "".join([chr(int(u)) for u in unicode_as_array])
        acronym = str(row["_code"])
        text = row["__text"]
        print("adding currency: ", acronym + " " + text + " " + symbol)

        currency = Currency(symbol=symbol, acronym=acronym, text=text)
        db.session.add(currency)
    db.session.commit()


@app.cli.command("delete_currency_table_values")
def delete_currency():
    """
    Deletes all Currency entries from the database.

    Run with 'flask delete_currency_table_values'
    """
    currencies = db.session.query(Currency).all()
    for currency in currencies:
        db.session.delete(currency)
    db.session.commit()

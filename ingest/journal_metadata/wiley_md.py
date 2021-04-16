import pandas as pd
from app import db
from models.journal import Journal, JournalMetadata


def cleanse_wiley_data(df):
    """
    Iterates through each row of the CSV and removes unnecessary columns.
    Replaces NaN with None
    """
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df = df.where(pd.notnull(df), None)
    return df

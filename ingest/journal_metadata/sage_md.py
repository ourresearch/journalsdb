import pandas as pd


def cleanse_sage_data(df):
    """
    Iterates through each row of the CSV and removes unnecessary columns.
    Replaces NaN with None
    """
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df = df.where(pd.notnull(df), None)
    return df

import pandas as pd

from app import db
from models.journal import Journal, JournalMetadata

from ingest.journal_metadata.journal_metadata import JournalMetaDataImporter


def cleanse_data(df):
    """
    Iterates through each row of the CSV and confirms that the society_organization
    and society organization url have an equal number of ';' characters.

    Manually resolves conflicts
    """
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_colwidth", None)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    df.loc[0, "society_organization"] = df.loc[0, "society_organization"].replace(
        " , ", ";"
    )
    df.loc[2, "society_organization"] = df.loc[0, "society_organization"].replace(
        " and ", ";"
    )
    df.loc[11, "society_organization"] = df.loc[11, "society_organization"].replace(
        ", ", ";"
    )
    df.loc[11, "society_organization"] = df.loc[11, "society_organization"].replace(
        " and ", ";"
    )
    df.loc[17, "society_organization"] = df.loc[17, "society_organization"].replace(
        " & ", ";"
    )
    df.loc[
        19, "society_organization"
    ] = "The Society and College of Radiographers;the European Federation of Radiographer Societies"
    df.loc[20, "society_organization"] = df.loc[20, "society_organization"].replace(
        " and ", ";"
    )
    df.loc[34, "society_organization"] = df.loc[34, "society_organization"].replace(
        ", ", ";"
    )
    df.loc[34, "society_organization"] = df.loc[34, "society_organization"].replace(
        " and ", ";"
    )
    df.loc[54, "society_organization"] = df.loc[54, "society_organization"].replace(
        ", ", ";"
    )
    df.loc[54, "society_organization"] = df.loc[54, "society_organization"].replace(
        "; and ", ";"
    )
    df.loc[54, "society_organization_url"] = df.loc[
        54, "society_organization_url"
    ].replace(", and ", ";")
    df.loc[54, "society_organization_url"] = df.loc[
        54, "society_organization_url"
    ].replace(", ", ";")
    df.loc[228, "society_organization"] = df.loc[228, "society_organization"].replace(
        ";", ""
    )
    df.loc[290, "society_organization_url"] = df.loc[
        290, "society_organization_url"
    ].replace(" , ", ";")
    df.loc[294, "society_organization_url"] = (
        df.loc[294, "society_organization_url"] + ";https://imia-medinfo.org/wp/"
    )
    df.loc[310, "society_organization_url"] = df.loc[
        310, "society_organization_url"
    ].replace(" ", ";")
    df.loc[349, "society_organization_url"] = df.loc[
        349, "society_organization_url"
    ].replace(" ", ";")
    df.loc[398, "society_organization_url"] = df.loc[
        398, "society_organization_url"
    ].replace(" ", ";")
    df = df.where(pd.notnull(df), None)

    df_counts = df[["society_organization", "society_organization_url"]].applymap(
        lambda x: str.count(str(x), ";")
    )
    df_difference = df[
        df_counts["society_organization"] != df_counts["society_organization_url"]
    ]
    print(
        "Differences between society_organization_url and society_organization: ",
        len(df_difference),
    )
    return df


class ElsevierMD(JournalMetaDataImporter):
    def __init__(self, df):
        super().__init__(df)

    def update_society(self, row):
        """
        Creates a list of dictionaries to store in the journal's society journal
        information.

        Format
        [
            {
                "organization": Name,
                "url": https://url.com,
            },
        ]
        """
        society_organization = row["society_organization"]
        society_organization_url = row["society_organization_url"]
        if society_organization:
            self.md.is_society_journal = True
            self.org_list = [
                {"organization": s.strip()} for s in society_organization.split(";")
            ]
            if society_organization_url:
                url_list = [
                    {"url": s.strip()} for s in society_organization_url.split(";")
                ]
            else:
                url_list = [{"url": None}] * len(self.org_list)
            [self.org_list[i].update(url_list[i]) for i in range(0, len(self.org_list))]
            self.md.societies = self.org_list
        else:
            self.md.society_journal = False
            self.md.societies = None

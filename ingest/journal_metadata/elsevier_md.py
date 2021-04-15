import pandas as pd

from app import db
from models.journal import Journal, JournalMetadata


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


def ingest_journal_metadata(df):
    """
    Iterates through the CSV and saves journal metadata into the database.
    """
    for index, row in df.iterrows():
        issn = row["issn"]
        if issn:
            j = db.session.query(Journal).filter_by(issn_l=issn).one_or_none()
            if j:
                home_page_url = row["home_page_url"]
                author_instructions_url = row["author_instructions"]
                editorial_page_url = row["editorial_board"]
                facebook_url = row["facebook_url"]
                linkedin_url = row["linkedin_url"]
                twitter_url = row["twitter_page_url"]
                wikidata_url = row["wikidata_url"]
                society_organization = row["society_organization"]
                society_organization_url = row["society_organization_url"]
                md = (
                    db.session.query(JournalMetadata)
                    .filter_by(journal_id=j.id)
                    .one_or_none()
                )

                if not md:
                    md = JournalMetadata()
                    md.journal_id = j.id

                md.home_page_url = home_page_url
                md.author_instructions_url = author_instructions_url
                md.editorial_page_url = editorial_page_url
                md.facebook_url = facebook_url
                md.linkedin_url = linkedin_url
                md.twitter_url = twitter_url
                md.wikidata_url = wikidata_url

                update_society(md, society_organization, society_organization_url)
            else:
                print("Could not find Journal for ISSN: ", issn)
        db.session.add(md)
        db.session.commit()


def update_society(md, society_organization, society_organization_url):
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
    if society_organization:
        md.is_society_journal = True
        org_list = [
            {"organization": s.strip()} for s in society_organization.split(";")
        ]
        if society_organization_url:
            url_list = [{"url": s.strip()} for s in society_organization_url.split(";")]
        else:
            url_list = [{"url": None}] * len(org_list)
        [org_list[i].update(url_list[i]) for i in range(0, len(org_list))]
        md.society_journal_organizations = org_list
    else:
        md.society_journal = False
        md.society_journal_organizations = None

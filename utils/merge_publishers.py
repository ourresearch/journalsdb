import time

from app import app, db
from models.journal import Imprint, Publisher

ELSEVIER = "Elsevier"
SAGE = "SAGE"
SPRINGER_NATURE = "Springer Nature"
TAYLOR_FRANCIS = "Taylor & Francis"
WILEY = "Wiley"


@app.cli.command("merge_publishers")
def merge_publishers():
    set_core_publishers()
    set_imprints()
    combine_publishers()


def set_core_publishers():
    core_publishers = [
        ("Wiley (John Wiley & Sons)", WILEY),
        ("Informa UK (Taylor & Francis)", TAYLOR_FRANCIS),
        ("Springer-Verlag", SPRINGER_NATURE),
        ("SAGE Publications", SAGE),
    ]
    for p in core_publishers:
        publisher = Publisher.query.filter_by(name=p[0]).one_or_none()
        if publisher:
            print("setting publisher {} to {} (test)".format(publisher.name, p[1]))
            publisher.name = p[1]
    db.session.commit()


def set_imprints():
    imprints = [
        {
            "old": "Wiley",
            "imprint": "John Wiley & Sons",
            "publisher": WILEY,
        },
        {
            "old": "Wiley (Physiological Reports)",
            "imprint": "Physiological Reports",
            "publisher": WILEY,
        },
        {
            "old": "Wiley (AHRC Research Centre)",
            "imprint": "AHRC Research Centre",
            "publisher": WILEY,
        },
        {"old": "Wiley (Opulus Press)", "imprint": "Opulus Press", "publisher": WILEY},
        {
            "old": "Wiley (American Cancer Society)",
            "imprint": "American Cancer Society",
            "publisher": WILEY,
        },
        {
            "old": "Wiley (The Wildlife Society)",
            "imprint": "The Wildlife Society",
            "publisher": WILEY,
        },
        {
            "old": "Wiley (The Physiological Society)",
            "imprint": "The Physiological Society",
            "publisher": WILEY,
        },
        {
            "old": "Wiley (Canadian Academic Accounting Association)",
            "imprint": "Canadian Academic Accounting Association",
            "publisher": WILEY,
        },
        {
            "old": "Wiley (Robotic Publications)",
            "imprint": "Robotic Publications",
            "publisher": WILEY,
        },
        {
            "old": "Wiley (Blackwell Publishing)",
            "imprint": "Blackwell Publishing",
            "publisher": WILEY,
        },
        {
            "old": "Informa UK (Informa Healthcare)",
            "imprint": "Informa Healthcare",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Informa UK (Swets & Zeitlinger Publishers)",
            "imprint": "Swets & Zeitlinger Publishers",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Informa UK (American Statistical Association)",
            "imprint": "American Statistical Association",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Informa UK (Heldref Publications)",
            "imprint": "Heldref Publications",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Informa UK (Librapharm)",
            "imprint": "Librapharm",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Informa UK (Haworth Press, Inc.,)",
            "imprint": "Haworth Press Inc.",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Informa UK (Marcel Dekker)",
            "imprint": "Marcel Dekker",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Informa UK (Ashley Publications)",
            "imprint": "Ashley Publications",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Informa UK (Routledge)",
            "imprint": "Routledge",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Informa UK (Beech Tree Publishing)",
            "imprint": "Beech Tree Publishing",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Maney Publishing",
            "imprint": "Maney Publishing",
            "publisher": TAYLOR_FRANCIS,
        },
        {
            "old": "Springer (Biomed Central Ltd.)",
            "imprint": "Biomed Central Ltd.",
            "publisher": SPRINGER_NATURE,
        },
        {
            "old": "Springer - Global Science Journals",
            "imprint": "Global Science Journals",
            "publisher": SPRINGER_NATURE,
        },
        {
            "old": "Springer - Psychonomic Society",
            "imprint": "Psychonomic Society",
            "publisher": SPRINGER_NATURE,
        },
        {
            "old": "Springer (Kluwer Academic Publishers)",
            "imprint": "Kluwer Academic Publishers",
            "publisher": SPRINGER_NATURE,
        },
        {
            "old": "Springer Fachmedien Wiesbaden GmbH",
            "imprint": "Springer Fachmedien Wiesbaden GmbH",
            "publisher": SPRINGER_NATURE,
        },
        {
            "old": "Springer - RILEM Publishing",
            "imprint": "RILEM Publishing",
            "publisher": SPRINGER_NATURE,
        },
        {
            "old": "Springer - Society of Surgical Oncology",
            "imprint": "Society of Surgical Oncology",
            "publisher": SPRINGER_NATURE,
        },
        {"old": "Springer - Adis", "imprint": "Adis", "publisher": SPRINGER_NATURE},
        {
            "old": "Springer - Humana Press",
            "imprint": "Humana Press",
            "publisher": SPRINGER_NATURE,
        },
        {
            "old": "Springer Science and Business Media LLC",
            "imprint": "Springer Science and Business Media LLC",
            "publisher": SPRINGER_NATURE,
        },
        {
            "old": "Elsevier - Academic Press",
            "imprint": "Academic Press",
            "publisher": ELSEVIER,
        },
        {
            "old": "Elsevier - WB Saunders",
            "imprint": "WB Saunders",
            "publisher": ELSEVIER,
        },
        {"old": "Elsevier - Mosby", "imprint": "Mosby", "publisher": ELSEVIER},
        {
            "old": "Elsevier - CIG Media Group LP",
            "imprint": "CIG Media Group LP",
            "publisher": ELSEVIER,
        },
        {
            "old": "Elsevier - International Federation of Automatic Control (IFAC)",
            "imprint": "International Federation of Automatic Control (IFAC)",
            "publisher": ELSEVIER,
        },
        {
            "old": "Elsevier - Medicine Publishing Company",
            "imprint": "Medicine Publishing Company",
            "publisher": ELSEVIER,
        },
        {
            "old": "Elsevier - Wilderness Medical Society",
            "imprint": "Wilderness Medical Society",
            "publisher": ELSEVIER,
        },
        {
            "old": "Elsevier- Churchill Livingstone",
            "imprint": "Churchill Livingstone",
            "publisher": ELSEVIER,
        },
    ]

    for i in imprints:
        publisher = Publisher.query.filter_by(name=i["old"]).one_or_none()
        imprint = Imprint.query.filter_by(name=i["imprint"]).one_or_none()
        if not imprint:
            new_publisher = Publisher.query.filter_by(name=i["publisher"]).one()
            imprint = Imprint(name=i["imprint"], publisher_id=new_publisher.id)
            db.session.add(imprint)
            db.session.commit()

        print(publisher.name, len(publisher.journals))
        time.sleep(1)

        for journal in publisher.journals:
            print(
                "setting journal {} imprint to {}".format(journal.title, i["imprint"])
            )
            journal.imprint = imprint
        db.session.commit()


def combine_publishers():
    publishers = [
        ("Wiley (Physiological Reports)", WILEY),
        ("Wiley (AHRC Research Centre)", WILEY),
        ("Wiley (Opulus Press)", WILEY),
        ("Wiley (American Cancer Society)", WILEY),
        ("Wiley (The Wildlife Society)", WILEY),
        ("Wiley (The Physiological Society)", WILEY),
        (
            "Wiley (Canadian Academic Accounting Association)",
            WILEY,
        ),
        ("Wiley (Robotic Publications)", WILEY),
        ("Wiley (Blackwell Publishing)", WILEY),
        ("Informa UK (Informa Healthcare)", TAYLOR_FRANCIS),
        ("Informa UK (Swets & Zeitlinger Publishers)", TAYLOR_FRANCIS),
        (
            "Informa UK (American Statistical Association)",
            TAYLOR_FRANCIS,
        ),
        ("Informa UK (Heldref Publications)", TAYLOR_FRANCIS),
        ("Informa UK (Librapharm)", TAYLOR_FRANCIS),
        ("Informa UK (Haworth Press, Inc.,)", TAYLOR_FRANCIS),
        ("Informa UK (Marcel Dekker)", TAYLOR_FRANCIS),
        ("Informa UK (Ashley Publications)", TAYLOR_FRANCIS),
        ("Informa UK (Routledge)", TAYLOR_FRANCIS),
        ("Informa UK (Beech Tree Publishing)", TAYLOR_FRANCIS),
        ("Maney Publishing", TAYLOR_FRANCIS),
        ("Springer (Biomed Central Ltd.)", SPRINGER_NATURE),
        ("Springer - Global Science Journals", SPRINGER_NATURE),
        ("Springer - Psychonomic Society", SPRINGER_NATURE),
        ("Springer (Kluwer Academic Publishers)", SPRINGER_NATURE),
        ("Springer Fachmedien Wiesbaden GmbH", SPRINGER_NATURE),
        ("Springer - RILEM Publishing", SPRINGER_NATURE),
        ("Springer - Society of Surgical Oncology", SPRINGER_NATURE),
        ("Springer - Adis", SPRINGER_NATURE),
        ("Springer - Humana Press", SPRINGER_NATURE),
        (
            "Springer Science and Business Media LLC",
            SPRINGER_NATURE,
        ),
        ("Elsevier - Academic Press", ELSEVIER),
        ("Elsevier - WB Saunders", ELSEVIER),
        ("Elsevier - Mosby", ELSEVIER),
        ("Elsevier - CIG Media Group LP", ELSEVIER),
        (
            "Elsevier - International Federation of Automatic Control (IFAC)",
            ELSEVIER,
        ),
        ("Elsevier - Medicine Publishing Company", ELSEVIER),
        ("Elsevier - Wilderness Medical Society", ELSEVIER),
        ("Elsevier- Churchill Livingstone", ELSEVIER),
    ]

    for p in publishers:
        old_publisher = Publisher.query.filter_by(name=p[0]).one_or_none()
        new_publisher = Publisher.query.filter_by(name=p[1]).one_or_none()
        for journal in old_publisher.journals:
            print(
                "setting journal {} from old publisher {} to new publisher {}".format(
                    journal.title, old_publisher.name, new_publisher.name
                )
            )
            journal.publisher_id = new_publisher.id
        db.session.commit()

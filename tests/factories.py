from app import db
from models.issn import ISSNMetaData
from models.journal import Journal, Publisher, JournalMetadata
from models.location import Country, Region
from models.price import SubscriptionPrice, APCPrice, Currency
from models.usage import RetractionSummary, OpenAccess, Repository


def import_api_test_data():
    country = Country(
        id=1,
        name="United States",
        iso="US",
        iso3="USA",
        continent_id=None,
        continent=None,
    )

    db.session.add(country)

    cur = Currency(
        id=1,
        symbol="abc",
        text="abcd",
        acronym="abc",
    )

    db.session.add(cur)

    p = Publisher(
        id=1,
        name="JMIR Publications Inc.",
        publisher_synonyms=None,
        uuid="fdsklsdjfkdf",
        sub_data_source="springer.com",
        apc_data_source="springerapc.com",
    )

    db.session.add(p)

    r = Region(
        name="Northern",
        publisher=p,
    )

    db.session.add(r)

    apc = APCPrice(
        id=1,
        price=200,
        year=1990,
        notes=None,
        country=country,
        currency=cur,
        region=r,
    )

    db.session.add(apc)

    apc2 = APCPrice(
        id=2,
        price=300,
        year=1991,
        notes=None,
        country=country,
        currency=cur,
        region=r,
    )

    db.session.add(apc2)

    apc3 = APCPrice(
        id=3,
        price=400,
        year=1992,
        notes=None,
        country=country,
        currency=cur,
        region=r,
    )

    db.session.add(apc3)

    pr = SubscriptionPrice(
        id=1,
        price=200.00,
        currency=cur,
        region=r,
        country=country,
        fte_from=20,
        fte_to=100,
        year=1990,
    )

    db.session.add(pr)

    pr2 = SubscriptionPrice(
        id=2,
        price=300.00,
        currency=cur,
        region=r,
        country=country,
        fte_from=100,
        fte_to=200,
        year=1991,
    )

    db.session.add(pr2)

    pr3 = SubscriptionPrice(
        id=3,
        price=400.00,
        currency=cur,
        region=r,
        country=country,
        fte_from=500,
        fte_to=600,
        year=1992,
    )

    db.session.add(pr3)

    md = ISSNMetaData(
        issn_l="2291-5222",
        issn_org_issns=["2291-5222"],
        issn_org_raw_api=None,
        crossref_issns=None,
        crossref_raw_api=None,
    )

    db.session.add(md)

    oa_one = OpenAccess(
        issn_l="2291-5222",
        title="open access title",
        year=2021,
        num_dois=151,
        num_open=151,
        open_rate=1,
        num_green=3,
        green_rate=0,
        num_bronze=0,
        bronze_rate=0,
        num_hybrid=2,
        hybrid_rate=0,
        num_gold=1,
        gold_rate=1,
        is_in_doaj=True,
        is_gold_journal=True,
    )

    db.session.add(oa_one)

    oa_two = OpenAccess(
        issn_l="2291-5222",
        title="open access title",
        year=2020,
        num_dois=624,
        num_open=624,
        open_rate=1,
        num_green=0,
        green_rate=0,
        num_bronze=0,
        bronze_rate=0,
        num_hybrid=2,
        hybrid_rate=0,
        num_gold=624,
        gold_rate=1,
        is_in_doaj=True,
        is_gold_journal=True,
    )

    db.session.add(oa_two)

    repo = Repository(
        issn_l="2291-5222",
        endpoint_id="0018d9899f05d098c16",
        repository_name="Hogskolan Ihalmstad",
        institution_name="Halmstad University",
        home_page="http://hh.diva-portal.org",
        pmh_url="http://hh.diva-portal.org/dice/oai",
        num_articles=1,
    )

    db.session.add(repo)

    repo_two = Repository(
        issn_l="2291-5222",
        endpoint_id="02515f20c30fa079b26",
        repository_name="Ghent University Academic Bibliography",
        institution_name="Ghent University",
        home_page="https://biblio.ugent.be",
        pmh_url="http://biblio.ugent.be/oai",
        num_articles=5,
    )

    db.session.add(repo_two)

    rs = RetractionSummary(
        id=1,
        issn="2291-5222",
        journal="MIR",
        year=1990,
        retractions=4,
        num_dois=3,
    )

    db.session.add(rs)

    j = Journal(
        id=1,
        issn_l="2291-5222",
        title="JMIR mhealth and uhealth",
        journal_synonyms=None,
        publisher=p,
        internal_publisher_id="JMIR",
        imprint_id=23,
        discount_waiver_exception=True,
        uuid="23",
        is_modified_title=True,
        apc_prices=[apc, apc2, apc3],
        author_permissions=[],
        imprint=None,
        issn_metadata=md,
        journal_metadata=[],
        permissions=None,
        subjects=[],
        subscription_prices=[pr, pr2, pr3],
    )

    db.session.add(j)
    db.session.commit()

    j_md = JournalMetadata(
        id=1,
        journal_id=1,
        home_page_url="www.homepage.com",
        author_instructions_url="Author Instructions",
        editorial_page_url="www.editorial.com",
        facebook_url="www.facebook.com",
        linkedin_url="www.linkedin.com",
        twitter_url="www.twitter.com",
        wikidata_url="www.wiki.com",
        is_society_journal=False,
        societies=None,
    )

    db.session.add(j_md)
    db.session.commit()

    md = ISSNMetaData(
        issn_l="1907-1760",
        issn_org_issns=["2460-6626", "1907-1760"],
        issn_org_raw_api=None,
        crossref_issns=None,
        crossref_raw_api=None,
    )

    db.session.add(md)

    p_two = Publisher(
        id=2,
        name="Universitas Andalas",
        publisher_synonyms=None,
        uuid="qrewerwr",
        sub_data_source=None,
        apc_data_source=None,
    )

    db.session.add(p_two)
    db.session.commit()

    j_two = Journal(
        id=2,
        issn_l="2460-6626",
        title="Jurnal peternakan Indonesia",
        journal_synonyms=None,
        publisher=p_two,
        internal_publisher_id="UA",
        imprint_id=23,
        discount_waiver_exception=True,
        uuid="234",
        is_modified_title=True,
        apc_prices=[],
        author_permissions=[],
        imprint=None,
        issn_metadata=md,
        journal_metadata=[],
        permissions=None,
        subjects=[],
        subscription_prices=[pr],
    )

    db.session.add(j_two)
    db.session.commit()

    p_wiley = Publisher(
        id=3,
        name="Wiley (Blackwell Publishing)",
        publisher_synonyms=None,
        uuid="ajdklcue",
        sub_data_source=None,
        apc_data_source=None,
    )

    db.session.add(p_wiley)

    md_wiley = ISSNMetaData(
        issn_l="1354-7798",
        issn_org_issns=["1354-7798"],
        issn_org_raw_api=None,
        crossref_issns=None,
        crossref_raw_api=None,
    )

    db.session.add(md_wiley)

    j_wiley = Journal(
        id=3,
        issn_l="1354-7798",
        title="European financial management",
        journal_synonyms=None,
        publisher=p_wiley,
        internal_publisher_id="EFM",
        imprint_id=27,
        discount_waiver_exception=True,
        uuid="23456798",
        is_modified_title=True,
        apc_prices=[],
        author_permissions=[],
        imprint=None,
        issn_metadata=md_wiley,
        journal_metadata=[],
        permissions=None,
        subjects=[],
        subscription_prices=[],
    )

    db.session.add(j_wiley)
    db.session.commit()
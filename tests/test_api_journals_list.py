from app import db
from models.journal import Publisher
from tests.conftest import NUMBER_OF_JOURNALS


class TestAPIJournalsList:
    """Full journals list endpoint (no pagination)."""

    def test_journals_no_attributes(self, api_client):
        rv = api_client.get("/journals")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["journals"]
        assert len(json_data["journals"]) == NUMBER_OF_JOURNALS
        sample = next(
            (item for item in json_data["journals"] if item["issn_l"] == "1907-1760"),
            None,
        )
        assert sample["issn_l"] == "1907-1760"

    def test_journals_with_attributes_no_synonyms(self, api_client):
        attrs = "issn_l,title,uuid,publisher_name,issns"
        rv = api_client.get("/journals?attrs={}".format(attrs))
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["count"] == NUMBER_OF_JOURNALS

        sample = next(
            (item for item in json_data["journals"] if item["issn_l"] == "1907-1760"),
            None,
        )
        assert sample["issn_l"] == "1907-1760"
        assert sample["publisher_name"] == "Universitas Andalas"
        assert "2460-6626" in sample["issns"]
        assert "1907-1760" in sample["issns"]
        assert sample["title"] == "Jurnal peternakan Indonesia"
        assert sample["uuid"]

    def test_journals_with_attributes_synonyms(self, api_client):
        attrs = "issn_l,journal_synonyms,publisher_synonyms"
        rv = api_client.get("/journals?attrs={}".format(attrs))
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["count"] == NUMBER_OF_JOURNALS

        sample = next(
            (item for item in json_data["journals"] if item["issn_l"] == "1907-1760"),
            None,
        )
        assert sample["issn_l"] == "1907-1760"
        assert sample["journal_synonyms"] is None
        assert sample["publisher_synonyms"] is None

    def test_journals_with_invalid_attributes(self, api_client):
        attrs = "issn_l,title,uuid,publisher_secrets,issns"
        rv = api_client.get("/journals?attrs={}".format(attrs))
        json_data = rv.get_json()
        assert rv.status_code == 400
        assert json_data["error"]

    def test_journals_with_publisher_filter(self, api_client):
        pubs = (
            db.session.query(Publisher).filter(Publisher.name.contains("Wiley")).all()
        )
        for p in pubs:
            p.publisher_synonyms = ["wiley"]
        db.session.commit()

        attrs = "issn_l,title,publisher_name"
        publisher_filter = "wiley"
        rv = api_client.get(
            "/journals?attrs={}&publisher_name={}".format(attrs, publisher_filter)
        )
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["count"] == 1
        sample = next(
            (item for item in json_data["journals"] if item["issn_l"] == "1354-7798"),
            None,
        )
        assert sample["issn_l"] == "1354-7798"
        assert sample["publisher_name"] == "Wiley (Blackwell Publishing)"
        assert sample["title"] == "European financial management"
        sample = next(
            (
                item
                for item in json_data["journals"]
                if item["publisher_name"] == "Universitas Andalas"
            ),
            None,
        )
        assert not sample

    def test_journals_with_invalid_pub_filter(self, api_client):
        attrs = "issn_l,title,publisher_name"
        publisher_filter = "Wiley (Blackwell Publashing)"
        rv = api_client.get(
            "/journals?attrs={}&publisher_name={}".format(attrs, publisher_filter)
        )
        json_data = rv.get_json()
        assert rv.status_code == 400
        assert json_data["error"]

    def test_journal_renamed(self, api_client):
        rv = api_client.get("/journals/2291-5222")
        json_data = rv.get_json()
        assert json_data["formerly_known_as"][0]["issn_l"] == "5577-4444"

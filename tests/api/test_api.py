from flask import request, url_for

from app import db
from models.journal import Publisher

NUMBER_OF_JOURNALS = 3


class TestAPI:
    def test_api_root(self, api_client):
        rv = api_client.get("/")
        msg = rv.get_json()["msg"]
        assert rv.status_code == 200
        assert msg == "Don't panic"

    def test_find_issn(self, api_client):
        rv = api_client.get("/journals/2291-5222")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["issn_l"] == "2291-5222"
        assert json_data["issns"] == ["2291-5222"]
        assert json_data["title"] == "JMIR mhealth and uhealth"
        assert json_data["publisher"] == "JMIR Publications Inc."

    def test_invalid_issn(self, api_client):
        rv = api_client.get("/journals/0000-0000")
        assert rv.status_code == 404

    def test_redirected_issn(self, api_client):
        api_client.get("/journals/2460-6626", follow_redirects=True)
        assert request.path == url_for("journal_detail", issn="1907-1760")

    def test_journals_detail(self, api_client):
        rv = api_client.get("/journals/2291-5222")
        assert rv.status_code == 200
        json_data = rv.get_json()
        assert json_data["issn_l"] == "2291-5222"
        assert json_data["issns"] == ["2291-5222"]
        assert json_data["title"] == "JMIR mhealth and uhealth"
        assert json_data["publisher"] == "JMIR Publications Inc."
        assert (
            json_data["open_access_history"]
            == "https://api.journalsdb.org/journals/2291-5222/open-access"
        )
        assert (
            json_data["repositories"]
            == "https://api.journalsdb.org/journals/2291-5222/repositories"
        )

    def test_journals_paged_no_params(self, api_client):
        rv = api_client.get("/journals-paged")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["results"]
        assert len(json_data["results"]) == NUMBER_OF_JOURNALS
        sample = next(
            (item for item in json_data["results"] if item["issn_l"] == "1907-1760"),
            None,
        )
        assert sample["issn_l"] == "1907-1760"

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

    def test_search_with_valid_query(self, api_client):
        query = "European financial management"
        rv = api_client.get("/journals/search?query={}".format(query))
        json_data = rv.get_json()
        assert rv.status_code == 200
        sample = [item for item in json_data if item["issn_l"] == "1354-7798"][0]
        assert sample["issn_l"] == "1354-7798"

    def test_search_with_no_query(self, api_client):
        rv = api_client.get("/journals/search")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data == "no results found"

    def test_open_access(self, api_client):
        rv = api_client.get("/journals/2291-5222/open-access")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert len(json_data["open_access"]) == 2
        assert json_data["open_access"][0]["year"] == 2021
        assert json_data["open_access"][1]["year"] == 2020
        summary = json_data["summary"]
        assert summary["num_dois"] == 775
        assert summary["num_green"] == 3
        assert summary["num_hybrid"] == 4

    def test_repositories(self, api_client):
        rv = api_client.get("/journals/2291-5222/repositories")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["issn_l"] == "2291-5222"
        assert json_data["journal_title"] == "JMIR mhealth and uhealth"
        assert len(json_data["repositories"]) == 2
        sample = next(
            (
                item
                for item in json_data["repositories"]
                if item["endpoint_id"] == "0018d9899f05d098c16"
            ),
            None,
        )
        assert sample
        assert sample["repository_name"] == "Hogskolan Ihalmstad"

    def test_journal_subscription_prices(self, api_client):
        rv = api_client.get("/journals-paged")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["results"]
        assert len(json_data["results"]) == NUMBER_OF_JOURNALS
        sample = next(
            (item for item in json_data["results"] if item["issn_l"] == "2291-5222"),
            None,
        )
        assert sample["issn_l"] == "2291-5222"
        assert sample["subscription_pricing"]
        assert sample["subscription_pricing"]["provenance"] == "springer.com"
        assert sample["subscription_pricing"]["prices"][0]["year"] == 1992
        assert sample["subscription_pricing"]["prices"][1]["year"] == 1991
        assert sample["subscription_pricing"]["prices"][0]["price"] == "400.00"

    def test_journal_apc_prices(self, api_client):
        rv = api_client.get("/journals-paged")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["results"]
        assert len(json_data["results"]) == NUMBER_OF_JOURNALS
        sample = next(
            (item for item in json_data["results"] if item["issn_l"] == "2291-5222"),
            None,
        )
        assert sample["issn_l"] == "2291-5222"
        assert sample["apc_pricing"]
        assert sample["apc_pricing"]["provenance"] == "springerapc.com"
        assert sample["apc_pricing"]["apc_prices"][0]["year"] == 1992
        assert sample["apc_pricing"]["apc_prices"][1]["year"] == 1991
        assert sample["apc_pricing"]["apc_prices"][0]["price"] == "400.00"

    def test_journals_paged_with_page_params(self, api_client):
        rv = api_client.get("/journals-paged?page=1&per-page=2")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["pagination"]["count"] == NUMBER_OF_JOURNALS
        assert json_data["pagination"]["page"] == 1
        assert json_data["pagination"]["per_page"] == 2
        assert json_data["pagination"]["pages"] == 2

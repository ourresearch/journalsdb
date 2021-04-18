from flask import request, url_for

from app import db
from models.journal import Publisher


class TestAPI:
    def test_api_root(self, client):
        rv = client.get("/")
        msg = rv.get_json()["msg"]
        assert rv.status_code == 200
        assert msg == "Don't panic"

    def test_find_issn(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        rv = client.get("/journals/2291-5222")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["issn_l"] == "2291-5222"
        assert json_data["issns"] == ["2291-5222"]
        assert json_data["title"] == "JMIR mhealth and uhealth"
        assert json_data["publisher"] == "JMIR Publications Inc."

    def test_invalid_issn(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        rv = client.get("/journals/0000-0000")
        assert rv.status_code == 404

    def test_redirected_issn(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        rv = client.get("/journals/2460-6626", follow_redirects=True)
        assert request.path == url_for("journal_detail", issn="1907-1760")

    def test_journals_no_attributes(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        rv = client.get("/journals")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["count"] == 13
        sample = next(
            (item for item in json_data["journals"] if item["issn_l"] == "1907-1760"),
            None,
        )
        assert sample["issn_l"] == "1907-1760"

    def test_journals_with_attributes_no_synonyms(
        self, client, run_import_issns_with_api
    ):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        attrs = "issn_l,title,uuid,publisher_name,issns"
        rv = client.get("/journals?attrs={}".format(attrs))
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["count"] == 13

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

    def test_journals_with_attributes_synonyms(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        attrs = "issn_l,journal_synonyms,publisher_synonyms"
        rv = client.get("/journals?attrs={}".format(attrs))
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["count"] == 13

        sample = next(
            (item for item in json_data["journals"] if item["issn_l"] == "1907-1760"),
            None,
        )
        assert sample["issn_l"] == "1907-1760"
        assert sample["journal_synonyms"] is None
        assert sample["publisher_synonyms"] is None

    def test_journals_with_invalid_attributes(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        attrs = "issn_l,title,uuid,publisher_secrets,issns"
        rv = client.get("/journals?attrs={}".format(attrs))
        json_data = rv.get_json()
        assert rv.status_code == 400
        assert json_data["error"]

    def test_journals_with_publisher_filter(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        pubs = (
            db.session.query(Publisher).filter(Publisher.name.contains("Wiley")).all()
        )
        for p in pubs:
            p.publisher_synonyms = ["wiley"]
        db.session.commit()

        attrs = "issn_l,title,publisher_name"
        filter = "wiley"
        rv = client.get("/journals?attrs={}&publisher_name={}".format(attrs, filter))
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

    def test_journals_with_invalid_pub_filter(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        attrs = "issn_l,title,publisher_name"
        filter = "Wiley (Blackwell Publashing)"
        rv = client.get("/journals?attrs={}&publisher_name={}".format(attrs, filter))
        json_data = rv.get_json()
        assert rv.status_code == 400
        assert json_data["error"]

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

    def test_journals(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")
        rv = client.get("/journals")
        json_data = rv.get_json()
        assert rv.status_code == 200
        sample = next(
            (item for item in json_data["journals"] if item["issn_l"] == "1907-1760"),
            None,
        )
        assert sample

        attrs = "issn_l,title"
        rv = client.get("/journals?attrs={}".format(attrs))
        json_data = rv.get_json()
        assert rv.status_code == 200

        attrs = "issn_l,title,uuid,publisher_name,publisher_synonyms,issns"
        rv = client.get("/journals?attrs={}".format(attrs))
        json_data = rv.get_json()
        assert rv.status_code == 200

        sample = next(
            (item for item in json_data["journals"] if item["issn_l"] == "1907-1760"),
            None,
        )
        assert sample["publisher_name"] == "Universitas Andalas"
        assert sample["synonyms"] == None
        assert "2460-6626" in sample["issns"]
        assert "1907-1760" in sample["issns"]
        assert sample["title"] == "Jurnal peternakan Indonesia"
        assert sample["uuid"]

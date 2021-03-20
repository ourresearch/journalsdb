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

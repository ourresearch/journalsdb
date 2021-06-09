class TestAPIMisc:
    """Misc API tests."""

    def test_api_root(self, api_client):
        rv = api_client.get("/")
        msg = rv.get_json()["msg"]
        assert rv.status_code == 200
        assert msg == "Don't panic"

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

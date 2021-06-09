class TestAPIJournalSearch:
    """Journal search."""

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

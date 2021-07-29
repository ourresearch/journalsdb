from tests.conftest import NUMBER_OF_JOURNALS


class TestAPIJournalsPaged:
    """Paginated journals listing: /journals-paged?page=<>&per-page=<>"""

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

    def test_journals_paged_with_page_params(self, api_client):
        rv = api_client.get("/journals-paged?page=1&per-page=2")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["pagination"]["count"] == NUMBER_OF_JOURNALS
        assert json_data["pagination"]["page"] == 1
        assert json_data["pagination"]["per_page"] == 2
        assert json_data["pagination"]["pages"] == 2

    def test_journals_paged_renamed_merged(self, api_client):
        rv = api_client.get("/journals-paged")
        json_data = rv.get_json()
        sample = next(
            (item for item in json_data["results"] if item["issn_l"] == "2291-5222"),
            None,
        )
        assert sample["total_dois"] == 4
        assert sample["dois_by_issued_year"] == [[2021, 2], [2020, 2]]

    def test_journals_paged_renamed_no_merge(self, api_client):
        rv = api_client.get("/journals-paged?merge=false")
        json_data = rv.get_json()
        sample = next(
            (item for item in json_data["results"] if item["issn_l"] == "2291-5222"),
            None,
        )
        assert sample["total_dois"] == 2
        assert sample["dois_by_issued_year"] == [[2021, 2]]

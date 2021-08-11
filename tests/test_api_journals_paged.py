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

    def test_journals_paged_fields(self, api_client):
        """
        Ensure we are displaying the correct top-level fields in the correct order.
        """
        rv = api_client.get("/journals-paged")
        json_data = rv.get_json()
        sample = next(
            (item for item in json_data["results"] if item["issn_l"] == "1907-1760"),
            None,
        )
        top_level_keys = [
            "issn_l",
            "issns",
            "title",
            "publisher",
            "journal_metadata",
            "total_dois",
            "dois_by_issued_year",
            "sample_dois",
            "subscription_pricing",
            "apc_pricing",
            "open_access",
            "status",
            "status_as_of",
        ]

        i = 0
        for key in sample.keys():
            assert key == top_level_keys[i]
            i += 1

    def test_journals_paged_fields_renamed_current(self, api_client):
        """
        Ensure we are displaying the correct top-level fields in the correct order.
        New journals that have been renamed and are the current journal have an extra
        field called formerly_known_as.
        """
        rv = api_client.get("/journals-paged")
        json_data = rv.get_json()
        sample = next(
            (item for item in json_data["results"] if item["issn_l"] == "2291-5222"),
            None,
        )
        top_level_keys = [
            "issn_l",
            "issns",
            "title",
            "publisher",
            "journal_metadata",
            "formerly_known_as",
            "total_dois",
            "dois_by_issued_year",
            "sample_dois",
            "subscription_pricing",
            "apc_pricing",
            "open_access",
            "status",
            "status_as_of",
        ]

        i = 0
        for key in sample.keys():
            assert key == top_level_keys[i]
            i += 1

    def test_journals_paged_fields_renamed_former(self, api_client):
        """
        Ensure we are displaying the correct top-level fields in the correct order.
        Old journals that have been renamed have an extra field called currently_known_as.
        """
        rv = api_client.get("/journals-paged")
        json_data = rv.get_json()
        sample = next(
            (item for item in json_data["results"] if item["issn_l"] == "5577-4444"),
            None,
        )
        top_level_keys = [
            "issn_l",
            "issns",
            "title",
            "publisher",
            "journal_metadata",
            "currently_known_as",
            "total_dois",
            "dois_by_issued_year",
            "sample_dois",
            "subscription_pricing",
            "apc_pricing",
            "open_access",
            "status",
            "status_as_of",
        ]

        i = 0
        for key in sample.keys():
            assert key == top_level_keys[i]
            i += 1

    def test_journals_paged_pagination_headers_default(self, api_client):
        rv = api_client.get("/journals-paged")
        assert "Link" in rv.headers
        link_header_actual = rv.headers["Link"]
        link_header_expected = (
            '<https://api.journalsdb.org/journals-paged?page=1&per-page=100>; rel="first"'
            ',<https://api.journalsdb.org/journals-paged?page=1&per-page=100>; rel="last"'
        )
        assert link_header_actual == link_header_expected

    def test_journals_paged_pagination_headers_with_query_params(self, api_client):
        rv = api_client.get("/journals-paged?page=2&per-page=1")
        assert "Link" in rv.headers
        link_header_actual = rv.headers["Link"]
        link_header_expected = (
            "<https://api.journalsdb.org/journals-paged?page=1&per-page=1>; "
            'rel="first",<https://api.journalsdb.org/journals-paged?page=4&per-page=1>; '
            'rel="last",<https://api.journalsdb.org/journals-paged?page=1&per-page=1>; '
            'rel="prev",<https://api.journalsdb.org/journals-paged?page=3&per-page=1>; '
            'rel="next"'
        )
        assert link_header_actual == link_header_expected

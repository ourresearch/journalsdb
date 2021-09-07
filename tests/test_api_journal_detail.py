from flask import request, url_for


class TestAPIJournalDetail:
    """Journal detail: /journals/<issn>."""

    def test_invalid_issn(self, api_client):
        rv = api_client.get("/journals/0000-0000")
        assert rv.status_code == 404

    def test_redirected_issn(self, api_client):
        api_client.get("/journals/2460-6626", follow_redirects=True)
        assert request.path == url_for("journal_detail", issn="1907-1760")

    def test_journal_detail(self, api_client):
        rv = api_client.get("/journals/2291-5222")
        assert rv.status_code == 200
        json_data = rv.get_json()
        assert json_data["issn_l"] == "2291-5222"
        assert json_data["issns"] == ["2291-5222"]
        assert json_data["title"] == "JMIR mhealth and uhealth"
        assert json_data["publisher"] == "JMIR Publications Inc."
        assert (
            json_data["open_access_history"]
            == "http://localhost/journals/2291-5222/open-access"
        )
        assert (
            json_data["repositories"]
            == "http://localhost/journals/2291-5222/repositories"
        )

    def test_journal_detail_fields(self, api_client):
        """
        Ensure we are displaying the correct top-level fields in the correct order.
        """
        rv = api_client.get("/journals/1907-1760")
        json_data = rv.get_json()
        top_level_keys = [
            "id",
            "issn_l",
            "issns",
            "title",
            "publisher",
            "previous_issn_ls",
            "other_titles",
            "journal_metadata",
            "total_dois",
            "dois_by_issued_year",
            "sample_dois",
            "subscription_pricing",
            "apc_pricing",
            "open_access",
            "status",
            "status_as_of",
            "open_access_history",
            "repositories",
            "readership",
            "author_permissions",
            "retractions",
        ]

        i = 0
        for key in json_data.keys():
            assert key == top_level_keys[i]
            i += 1

    def test_journal_renamed_merged_dois_by_year(self, api_client):
        rv = api_client.get("/journals/2291-5222")
        json_data = rv.get_json()
        assert json_data["total_dois"] == 4

    def test_journal_renamed_merged_total_dois(self, api_client):
        rv = api_client.get("/journals/2291-5222")
        json_data = rv.get_json()
        assert json_data["dois_by_issued_year"] == [[2021, 2], [2020, 2]]

    def test_journal_renamed_merge_flag(self, api_client):
        rv = api_client.get("/journals/2291-5222?merge=true")
        json_data = rv.get_json()
        assert json_data["total_dois"] == 4
        assert json_data["dois_by_issued_year"] == [[2021, 2], [2020, 2]]

    def test_journal_renamed_no_merge(self, api_client):
        rv = api_client.get("/journals/2291-5222?merge=false")
        json_data = rv.get_json()
        assert json_data["total_dois"] == 2
        assert json_data["dois_by_issued_year"] == [[2021, 2]]

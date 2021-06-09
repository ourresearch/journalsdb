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
            == "https://api.journalsdb.org/journals/2291-5222/open-access"
        )
        assert (
            json_data["repositories"]
            == "https://api.journalsdb.org/journals/2291-5222/repositories"
        )

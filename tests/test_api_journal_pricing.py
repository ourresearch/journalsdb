class TestAPIJournalPricing:
    """Subscription and APC pricing."""

    def test_journal_subscription_prices(self, api_client):
        rv = api_client.get("/journals-paged")
        json_data = rv.get_json()
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

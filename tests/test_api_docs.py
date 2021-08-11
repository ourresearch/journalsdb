def test_api_docs(api_client):
    rv = api_client.get("/apidocs", follow_redirects=True)
    assert rv.status_code == 200
    assert b"JournalsDB API Docs" in rv.data

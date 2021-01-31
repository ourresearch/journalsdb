import pytest

from views import app
from app import db


@pytest.fixture
def client():
    import requests_cache

    requests_cache.install_cache("test_cache")

    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/journalsdb_test"
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            yield client
            # cleanup
            db.session.remove()
            db.drop_all()

import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# error reporting with sentry
sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"), integrations=[FlaskIntegration()])

app = Flask(__name__)
CORS(app)

# swagger
template = {
    "swagger": "2.0",
    "info": {"title": "JournalsDB API", "description": "", "version": "0.1"},
}
swagger = Swagger(app, template=template)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


with app.app_context():
    # needed to make CLI ingest work
    from ingest.author_permissions import *
    from ingest.issn import *
    from ingest.open_access import *
    from ingest.readership import *
    from ingest.repositories import *
    from ingest.locations import *
    from ingest.currency import *
    from ingest.retraction_watch import *
    from ingest.apc.import_apc_pricing import *
    from ingest.subscription.import_subscription_pricing import *
    import views

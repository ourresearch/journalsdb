from datetime import datetime

from marshmallow import fields

from app import ma
from models.author_permissions import AuthorPermissions
from models.usage import ExtensionRequests, OpenAccess, Repository


class AuthorPermissionsSchema(ma.SQLAlchemyAutoSchema):
    provenance = fields.Function(
        lambda obj: "https://shareyourpaper.org/permissions/about#data"
    )

    class Meta:
        model = AuthorPermissions
        ordered = True
        exclude = ["id", "created_at", "updated_at"]


class OpenAccessSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OpenAccess
        ordered = True
        exclude = ["issn_l", "title", "created_at", "updated_at"]


class ExtensionRequestsSchema(ma.SQLAlchemyAutoSchema):
    month = fields.Function(lambda obj: datetime.strftime(obj.month, "%B"))
    year = fields.Function(lambda obj: datetime.strftime(obj.month, "%Y"))
    requests = fields.Integer()

    class Meta:
        model = ExtensionRequests
        ordered = True
        fields = ("month", "year", "requests")


class RepositorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Repository
        ordered = True

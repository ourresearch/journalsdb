from datetime import datetime

from marshmallow import fields

from app import ma
from models.author_permissions import AuthorPermissions
from models.usage import Citation, ExtensionRequests, OpenAccess, Repository


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


class CitationsSchema(ma.SQLAlchemyAutoSchema):
    citations_by_year = fields.List(
        fields.List(fields.Integer), attribute="citations_by_year_sorted"
    )
    citations_per_article = fields.List(
        fields.List(fields.Float), attribute="citations_per_article_sorted"
    )

    class Meta:
        model = Citation
        ordered = True
        fields = ("citations_by_year", "citations_per_article")


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

from marshmallow import fields

from app import ma
from models.journal import Journal, JournalMetadata


class JournalSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Journal
        fields = ("issn_l", "title")


class JournalMetadataSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = JournalMetadata
        ordered = True
        exclude = ["id", "created_at", "updated_at"]


class FormerRenamedSchema(ma.Schema):
    issn_l = fields.Function(lambda obj: obj.former_journal.issn_l)
    title = fields.Function(lambda obj: obj.former_journal.title)
    url = ma.URLFor(
        "journal_detail",
        values=dict(issn="<former_journal.issn_l>", redirect="false", _external=True),
    )

    class Meta:
        ordered = True


class CurrentRenamedSchema(ma.Schema):
    issn_l = fields.String()
    title = fields.String()
    url = ma.URLFor("journal_detail", values=dict(issn="<issn_l>", _external=True))

    class Meta:
        ordered = True

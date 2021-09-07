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

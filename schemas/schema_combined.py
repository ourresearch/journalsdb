from marshmallow import fields, post_dump

from app import ma
from schemas.schema_price import (
    APCPriceSchema,
    MiniBundleSchema,
    SubscriptionPriceSchema,
)
from models.usage import RetractionSummary
from schemas.schema_journal import (
    CurrentRenamedSchema,
    FormerRenamedSchema,
    JournalMetadataSchema,
)
from schemas.schema_usage import (
    AuthorPermissionsSchema,
    ExtensionRequestsSchema,
    OpenAccessSchema,
)


class JournalListSchema(ma.Schema):
    """
    Schema for journals-paged.
    """

    issn_l = fields.String()
    issns = fields.List(fields.String())
    title = fields.String()
    publisher = fields.String(attribute="publisher.name", default=None)
    journal_metadata = fields.Nested(JournalMetadataSchema, many=True)

    # formerly / currently known as
    journals_renamed = fields.Nested(
        FormerRenamedSchema, many=True, data_key="formerly_known_as"
    )
    current_journal = fields.Nested(CurrentRenamedSchema, data_key="currently_known_as")

    # doi stats
    total_dois = fields.Integer(attribute="doi_counts.total_dois", default=None)
    dois_by_issued_year = fields.List(
        fields.List(fields.Integer),
        attribute="doi_counts.dois_by_year_sorted",
        default=[],
    )
    sample_dois = fields.List(
        fields.String, attribute="doi_counts.sample_doi_urls", default=None
    )

    # pricing
    sub_data_source = fields.Function(
        lambda obj: obj.publisher.sub_data_source if obj.publisher else None
    )
    apc_data_source = fields.Function(
        lambda obj: obj.publisher.apc_data_source if obj.publisher else None
    )
    subscription_prices = fields.Nested(
        SubscriptionPriceSchema, many=True, data_key="subscription_pricing"
    )
    apc_prices = fields.Nested(APCPriceSchema, many=True, data_key="apc_pricing")
    mini_bundles = fields.Nested(MiniBundleSchema, many=True)
    open_access_recent = fields.Nested(
        OpenAccessSchema,
        data_key="open_access",
    )
    status = fields.String(attribute="status.value")
    status_as_of = fields.DateTime(format="%Y-%m-%d", attribute="status_as_of")

    @post_dump()
    def move_provenance(self, data, many, **kwargs):
        """
        Moves provenance under the appropriate price dict.
        """
        if "subscription_pricing" in data:
            data["subscription_pricing"]["provenance"] = data["sub_data_source"]
            del data["sub_data_source"]
        if "apc_pricing" in data:
            data["apc_pricing"]["provenance"] = data["apc_data_source"]
            del data["apc_data_source"]
        return data

    @post_dump()
    def move_mini_bundle(self, data, many, **kwargs):
        """
        Moves mini bundles under subscription pricing.
        """
        if "subscription_pricing" in data:
            data["subscription_pricing"]["mini_bundles"] = data["mini_bundles"]
            del data["mini_bundles"]
        return data

    @post_dump()
    def remove_null_former_current_fields(self, data, many, **kwargs):
        if "formerly_known_as" in data and len(data["formerly_known_as"]) == 0:
            del data["formerly_known_as"]
        if "currently_known_as" in data and data["currently_known_as"] is None:
            del data["currently_known_as"]
        return data

    class Meta:
        ordered = True


class JournalDetailSchema(JournalListSchema):
    """
    Schema for journal detail view that adds additional fields to JournalListSchema.
    """

    open_access_history = ma.URLFor(
        "open_access", values=dict(issn="<issn_l>", _external=True)
    )
    repositories = ma.URLFor(
        "repositories", values=dict(issn_l="<issn_l>", _external=True)
    )
    extension_requests = fields.Nested(
        ExtensionRequestsSchema, many=True, data_key="readership"
    )
    permissions = fields.Nested(AuthorPermissionsSchema, data_key="author_permissions")
    retractions = fields.Function(
        lambda obj: RetractionSummary.retractions_by_year(obj.issn_l)
    )

    class Meta:
        ordered = True

from marshmallow import fields, post_dump

from app import ma
from schemas.schema_price import (
    APCMetadataSchema,
    APCPriceSchema,
    MiniBundleSchema,
    SubscriptionPriceSchema,
)
from models.usage import RetractionSummary
from schemas.custom_fields import DefaultList
from schemas.schema_journal import JournalMetadataSchema
from schemas.schema_usage import (
    AuthorPermissionsSchema,
    ExtensionRequestsSchema,
    OpenAccessSchema,
)


class JournalListSchema(ma.Schema):
    """
    Schema for journals-paged.
    """

    id = fields.String(attribute="uuid")
    issn_l = fields.String()
    issns = fields.List(fields.String())
    title = fields.String()
    publisher = fields.String(attribute="publisher.name", dump_default=None)
    previous_issn_ls = DefaultList(
        fields.String, attribute="issn_metadata.previous_issn_ls"
    )
    other_titles = DefaultList(fields.String)
    journal_metadata = fields.Nested(JournalMetadataSchema, many=True)

    # doi stats
    total_dois = fields.Method("get_total_dois", dump_default=None)
    dois_by_issued_year = fields.Method("get_dois_by_year", dump_default=None)
    sample_dois = fields.List(
        fields.String, attribute="doi_counts.sample_doi_urls", dump_default=None
    )

    # pricing
    sub_data_source = fields.Function(
        lambda obj: obj.publisher.sub_data_source if obj.publisher else None
    )
    apc_source = fields.String()
    apc_metadata = fields.Nested(APCMetadataSchema)
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

    def get_total_dois(self, obj):
        merge_records = self.context.get("merge")
        if merge_records:
            return obj.total_dois_merged
        else:
            return obj.total_dois_single

    def get_dois_by_year(self, obj):
        merge_records = self.context.get("merge")
        if merge_records:
            return obj.dois_by_year_merged or []
        else:
            return obj.dois_by_year_single or []

    @post_dump()
    def move_provenance(self, data, many, **kwargs):
        """
        Moves provenance and apc metadata under the appropriate price dict.
        """
        if "subscription_pricing" in data:
            data["subscription_pricing"]["provenance"] = data["sub_data_source"]
            del data["sub_data_source"]
        if "apc_pricing" in data:
            data["apc_pricing"]["apc_metadata"] = data["apc_metadata"]
            data["apc_pricing"]["provenance"] = data["apc_source"]
            del data["apc_source"]
            del data["apc_metadata"]
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

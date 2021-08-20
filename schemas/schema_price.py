from app import ma
from marshmallow import fields, post_dump
from models.price import APCMetadata, APCPrice, MiniBundle, SubscriptionPrice
from schemas.schema_journal import JournalSchema


class PriceSchema(ma.Schema):
    """
    Base schema for Subscription, APC, and Mini Bundle price schemas.
    """

    price = fields.Decimal(as_string=True)
    currency = fields.String(attribute="currency.acronym")
    region = fields.String(attribute="region.name", required=True)
    country = fields.String(attribute="country.name")


class APCPriceSchema(PriceSchema):
    apc_waived = fields.Boolean(data_key="waived")
    discount_reason = fields.String(data_key="discount_notes")

    class Meta:
        model = APCPrice
        fields = (
            "price",
            "currency",
            "region",
            "country",
            "year",
            "apc_waived",
            "discounted",
            "discount_notes",
        )
        ordered = True

    @post_dump(pass_many=True)
    def wrap_with_envelope(self, data, many, **kwargs):
        return {"apc_prices": data}


class APCMetadataSchema(ma.Schema):
    class Meta:
        model = APCMetadata
        fields = ("apc_fully_subsidized", "apc_subsidized_by", "notes")
        ordered = True


class MiniBundlePriceSchema(PriceSchema):
    class Meta:
        fields = (
            "price",
            "currency",
            "region",
            "country",
            "year",
        )
        ordered = True


class SubscriptionPriceSchema(PriceSchema):
    class Meta:
        model = SubscriptionPrice
        fields = (
            "fte_to",
            "fte_from",
            "price",
            "currency",
            "region",
            "country",
            "year",
        )
        ordered = True

    @post_dump(pass_many=True)
    def wrap_with_envelope(self, data, many, **kwargs):
        return {"prices": data}


class MiniBundleSchema(ma.Schema):
    mini_bundle_name = fields.String(attribute="name")
    journals = ma.Nested(
        JournalSchema, many=True, only=("issn_l", "title"), data_key="journals_included"
    )
    subscription_prices = ma.Nested(MiniBundlePriceSchema, many=True, data_key="prices")

    class Meta:
        model = MiniBundle
        fields = ("mini_bundle_name", "journals", "subscription_prices")
        ordered = True

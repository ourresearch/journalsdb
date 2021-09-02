from marshmallow import fields


class DefaultList(fields.List):
    """
    Displays an empty list if value is None.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return []
        return super()._serialize(value, attr, obj, **kwargs)

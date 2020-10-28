from rest_framework import fields


class EnumFieldSerializer(fields.CharField):
    def __init__(self, *args, **kwargs):
        self.mapping = kwargs.pop("mapping", {})
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        if value in self.mapping:
            return self.mapping[value]
        return value

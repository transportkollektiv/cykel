from rest_framework import fields, serializers


class EnumFieldSerializer(fields.CharField):
    def __init__(self, *args, **kwargs):
        self.mapping = kwargs.pop("mapping", {})
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        if value in self.mapping:
            return self.mapping[value]
        return value


class MappedChoiceField(serializers.ChoiceField):
    def __init__(self, *args, **kwargs):
        super(MappedChoiceField, self).__init__(*args, **kwargs)
        self.choice_strings_to_display = {
            str(key): value.name.lower() for key, value in self.choices.items()
        }

    def to_representation(self, value):
        if value is None:
            return value
        return self.choice_strings_to_display.get(str(value), value)

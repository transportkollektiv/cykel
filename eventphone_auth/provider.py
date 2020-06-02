from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class EventPhoneAccount(ProviderAccount):
    def to_str(self):
        default = super().to_str()
        return default


class EventPhoneProvider(OAuth2Provider):
    id = "eventphone"
    name = "EventPhone"
    package = "eventphone_auth"
    account_class = EventPhoneAccount

    def get_default_scope(self):
        return ["read:user"]

    def extract_uid(self, data):
        return str(data["id"])

    def extract_common_fields(self, data):
        fields = {
            "username": data.get("username"),
        }
        return fields


providers.registry.register(EventPhoneProvider)

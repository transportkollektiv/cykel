from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class OwncloudAccount(ProviderAccount):
    def to_str(self):
        default = super(OwncloudAccount, self).to_str()
        name = self.account.extra_data.get("user_id", "")
        return name or default


class OwncloudProvider(OAuth2Provider):
    id = "sub"
    name = "Owncloud"
    package = "owncloud_auth"
    account_class = OwncloudAccount

    def extract_uid(self, data):
        return str(data["user_id"])

    def extract_common_fields(self, data):
        fields = {
            "username": data.get("user_id"),
        }
        return fields


providers.registry.register(OwncloudProvider)

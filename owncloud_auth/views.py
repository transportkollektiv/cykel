from allauth.socialaccount import app_settings
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)

from .provider import OwncloudProvider


class OwncloudOAuth2Adapter(OAuth2Adapter):
    provider_id = OwncloudProvider.id
    settings = app_settings.PROVIDERS.get(provider_id, {})
    server = settings.get("SERVER", "https://owncloud.example.org")
    access_token_url = "{0}/index.php/apps/oauth2/api/v1/token".format(server)
    authorize_url = "{0}/index.php/apps/oauth2/authorize".format(server)
    basic_auth = True

    def complete_login(self, request, app, token, **kwargs):
        extra_data = {"user_id": kwargs["response"]["user_id"]}
        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(OwncloudOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(OwncloudOAuth2Adapter)

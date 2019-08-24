import requests

from allauth.socialaccount.providers.oauth2.views import (OAuth2Adapter,
                                                          OAuth2LoginView,
                                                          OAuth2CallbackView)
from .provider import EventPhoneProvider


class EventPhoneOAuth2Adapter(OAuth2Adapter):
    provider_id = EventPhoneProvider.id
    access_token_url = 'https://eventphone.api.dev.bike/token/'
    authorize_url = 'https://eventphone.api.dev.bike/authorize/'
    profile_url = 'https://eventphone.api.dev.bike/api/user/'

    def complete_login(self, request, app, token, **kwargs):
        resp = requests.get(self.profile_url,
                            params={'access_token': token.token})
        extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request,
                                                             extra_data)


oauth2_login = OAuth2LoginView.adapter_view(EventPhoneOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(EventPhoneOAuth2Adapter)

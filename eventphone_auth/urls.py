from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import EventPhoneProvider

urlpatterns = default_urlpatterns(EventPhoneProvider)

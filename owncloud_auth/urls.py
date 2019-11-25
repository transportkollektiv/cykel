from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import OwncloudProvider

urlpatterns = default_urlpatterns(OwncloudProvider)

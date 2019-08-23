"""cykel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from django.conf.urls.static import static

from rest_framework import routers, serializers, viewsets



from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.stackexchange.views import StackExchangeOAuth2Adapter
from allauth.socialaccount.providers.slack.views import SlackOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_auth.registration.views import SocialLoginView

class GithubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = "http://localhost:8080/?authservice=github" #TODO aus dem env holen
    client_class = OAuth2Client

class StackexchangeLogin(SocialLoginView):
    adapter_class = StackExchangeOAuth2Adapter
    callback_url = "http://localhost:8080/?authservice=stackexchange" #TODO aus dem env holen
    client_class = OAuth2Client

class SlackLogin(SocialLoginView):
    adapter_class = SlackOAuth2Adapter
    callback_url = "http://localhost:8080/?authservice=slack" #TODO aus dem env holen
    client_class = OAuth2Client


urlpatterns = [
    path('bikesharing/', include('bikesharing.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('gbfs/', include('gbfs.urls')),
    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
    url(r'^rest-auth/github/$', GithubLogin.as_view(), name='github_login'),
    url(r'^rest-auth/stackexchange/$', StackexchangeLogin.as_view(), name='stackexchange_login'),
    url(r'^rest-auth/slack/$', SlackLogin.as_view(), name='slack_login'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

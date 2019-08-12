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
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url, include
from rest_framework import routers, serializers, viewsets
from rest_framework.urlpatterns import format_suffix_patterns

from .views import gbfs
from .views import gbfsSystemInformation
from .views import GbfsFreeBikeStatusViewSet
from .views import GbfsStationInformationViewSet
from .views import GbfsStationStatusViewSet

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^gbfs/', include('rest_framework.urls', namespace='rest_framework_gbfs')),
    path('gbfs.json', gbfs),
    path('system_information.json', gbfsSystemInformation),
    path('free_bike_status.json', GbfsFreeBikeStatusViewSet.as_view()),
    path('station_information.json', GbfsStationInformationViewSet.as_view()),
    path('station_status.json', GbfsStationStatusViewSet.as_view()),
]

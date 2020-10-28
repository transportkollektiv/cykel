"""cykel URL Configuration.

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
from django.urls import include, path, re_path
from rest_framework import routers

from .views import (
    GbfsFreeBikeStatusViewSet,
    GbfsStationInformationViewSet,
    GbfsStationStatusViewSet,
    GbfsVehicleTypeViewSet,
    gbfs,
    gbfsSystemInformation,
)

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()

urlpatterns = [
    re_path(r"^", include(router.urls)),
    path("gbfs.json", gbfs),
    path("system_information.json", gbfsSystemInformation),
    path("free_bike_status.json", GbfsFreeBikeStatusViewSet.as_view()),
    path("station_information.json", GbfsStationInformationViewSet.as_view()),
    path("station_status.json", GbfsStationStatusViewSet.as_view()),
    path("vehicle_types.json", GbfsVehicleTypeViewSet.as_view()),
]

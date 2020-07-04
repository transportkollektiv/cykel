from django.conf.urls import url
from django.urls import include, path
from rest_framework import routers

from .views import (
    CurrentRentViewSet,
    LoginProviderViewSet,
    UserDetailsView,
    finish_rent,
    start_rent,
    updatebikelocation,
)

router = routers.DefaultRouter()

urlpatterns = [
    url(r"^", include(router.urls)),
    path("bike/updatelocation", updatebikelocation),
    path("rent/start", start_rent),
    path("rent/finish", finish_rent),
    path("rent/current", CurrentRentViewSet.as_view({"get": "list"})),
    path("user", UserDetailsView.as_view()),
    path("config/loginproviders", LoginProviderViewSet.as_view({"get": "list"})),
]

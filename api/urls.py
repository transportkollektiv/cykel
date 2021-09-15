from django.urls import include, path, re_path
from rest_framework import routers
from rest_framework.authtoken import views

from .views import (
    LoginProviderViewSet,
    MaintenanceViewSet,
    RentViewSet,
    UserDetailsView,
    updatebikelocation,
    ReservationViewSet,
    getAllowedDates,
    getAllowedTimes,
)

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"rent", RentViewSet, basename="rent")
router.register(r"maintenance", MaintenanceViewSet, basename="maintenance")
router.register(r"reservation", ReservationViewSet, basename="reservation")

urlpatterns = [
    re_path(r"^", include(router.urls)),
    path("bike/updatelocation", updatebikelocation),
    path("user", UserDetailsView.as_view()),
    path("config/loginproviders", LoginProviderViewSet.as_view({"get": "list"})),
    path("auth/token", views.obtain_auth_token),
    path("reservationdates/alloweddates", getAllowedDates),
    path("reservationdates/allowedtimes", getAllowedTimes),
]

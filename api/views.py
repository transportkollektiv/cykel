from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.sites.shortcuts import get_current_site
from django.utils.timezone import now
from preferences import preferences
from rest_framework import exceptions, generics, mixins, status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    BasePermission,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_api_key.permissions import HasAPIKey

from bikesharing.models import Bike, Location, LocationTracker, Rent, Station

from .serializers import (
    BikeSerializer,
    CreateRentSerializer,
    LocationTrackerUpdateSerializer,
    MaintenanceBikeSerializer,
    RentSerializer,
    SocialAppSerializer,
    StationSerializer,
    UserDetailsSerializer,
)


class BikeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer


class StationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class CanRentBikePermission(BasePermission):
    """The request is authenticated as a user and has add_rent permission."""

    message = "You cannot rent a bike at this time."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.has_perm("bikesharing.add_rent")


class CanUseMaintenancePermission(BasePermission):
    """The request is authenticated as a user and has maintenance
    permission."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.has_perm("bikesharing.maintain")


@permission_classes([IsAuthenticated, CanRentBikePermission])
class RentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    def get_serializer_class(self):
        if self.action == "create":
            return CreateRentSerializer
        else:
            return RentSerializer

    def get_queryset(self):
        user = self.request.user
        return Rent.objects.filter(user=user, rent_end=None)

    def create(self, request):
        resp = super().create(request)
        if resp.status_code != status.HTTP_201_CREATED:
            return resp
        # override output with RentSerializer
        rent = self.get_queryset().get(id=resp.data["id"])
        serializer = RentSerializer(rent, context={"request": request})
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        rent = self.get_object()

        lat = request.data.get("lat")
        lng = request.data.get("lng")

        if rent.user != request.user:
            return Response(
                {"error": "rent belongs to another user"},
                status=status.HTTP_403_PERMISSON_DENIED,
            )
        if rent.rent_end is not None:
            return Response(
                {"error": "rent was already finished"}, status=status.HTTP_410_GONE
            )

        end_location = None
        if lat and lng:
            end_location = Location.objects.create(
                bike=rent.bike, source=Location.Source.USER, reported_at=now()
            )
            end_location.geo = Point(float(lng), float(lat), srid=4326)
            end_location.save()

        rent.end(end_location)

        return Response({"success": True})

    @action(detail=True, methods=["post"])
    def unlock(self, request, pk=None):
        rent = self.get_object()

        if rent.user != request.user:
            return Response(
                {"error": "rent belongs to another user"},
                status=status.HTTP_403_PERMISSON_DENIED,
            )

        if rent.rent_end is not None:
            return Response(
                {"error": "rent was already finished"}, status=status.HTTP_410_GONE
            )

        try:
            data = rent.unlock()
        except Exception as e:
            print(e)
            return Response({"success": False})

        return Response({"success": True, "data": data})


@api_view(["POST"])
@permission_classes([HasAPIKey])
def updatebikelocation(request):
    device_id = request.data.get("device_id")
    if not (device_id):
        return Response({"error": "device_id missing"}, status=400)
    try:
        tracker = LocationTracker.objects.get(device_id=device_id)
    except LocationTracker.DoesNotExist:
        return Response({"error": "tracker does not exist"}, status=404)

    serializer = LocationTrackerUpdateSerializer(tracker, data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    serializer.save()

    lat = request.data.get("lat")
    lng = request.data.get("lng")
    accuracy = request.data.get("accuracy")
    loc = None

    if lat and lng:
        loc = Location.objects.create(source=Location.Source.TRACKER, reported_at=now())
        if tracker.bike:
            loc.bike = tracker.bike
        loc.geo = Point(float(lng), float(lat), srid=4326)
        loc.tracker = tracker
        if accuracy:
            loc.accuracy = accuracy
        loc.save()

    if tracker.bike:
        bike = tracker.bike
        bike.last_reported = now()

        if loc and not loc.internal:
            # check if bike is near station and assign it to that station
            # distance ist configured in prefernces
            max_distance = preferences.BikeSharePreferences.station_match_max_distance
            station_closer_than_Xm = Station.objects.filter(
                location__distance_lte=(loc.geo, D(m=max_distance)),
                status=Station.Status.ACTIVE,
            ).first()
            if station_closer_than_Xm:
                bike.current_station = station_closer_than_Xm
            else:
                bike.current_station = None

        bike.save()

    if not loc:
        return Response({"success": True, "warning": "lat/lng missing"})

    return Response({"success": True})


@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated, CanUseMaintenancePermission])
class MaintenanceViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["GET"])
    def mapdata(self, request):
        bikes = Bike.objects.filter(location__isnull=False).distinct()
        serializer = MaintenanceBikeSerializer(bikes, many=True)
        return Response(serializer.data)


class UserDetailsView(generics.RetrieveAPIView):
    """Reads UserModel fields Accepts GET method.

    Default accepted fields: username Default display fields: pk,
    username Read-only fields: pk Returns UserModel fields.
    """

    serializer_class = UserDetailsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        """Adding this method since it is sometimes called when using django-
        rest-swagger https://github.com/Tivix/django-rest-auth/issues/275."""
        return get_user_model().objects.none()


@permission_classes([AllowAny])
class LoginProviderViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """return the configured social login providers."""

    serializer_class = SocialAppSerializer

    def get_queryset(self):
        return SocialApp.objects.filter(sites__id=get_current_site(self.request).id)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    headers = {}
    if isinstance(exc, exceptions.APIException):
        if getattr(exc, "auth_header", None):
            headers["WWW-Authenticate"] = exc.auth_header

    errors = []
    if getattr(exc, "detail", None):
        if isinstance(exc.detail, list):
            errors.append({"detail": exc.detail})
        elif isinstance(exc.detail, dict):
            for key, value in exc.detail.items():
                if isinstance(value, list):
                    for item in value:
                        errors.append({"detail": item, "source": key})
                else:
                    errors.append({"detail": value, "source": key})
        else:
            errors.append({"detail": exc.detail})
    else:
        errors.append({"detail": str(exc)})

    messages = []
    for item in errors:
        if getattr(item["detail"], "code", None):
            item["code"] = item["detail"].code
        messages.append(item["detail"])

    data = {"errors": errors, "message": "\n".join(messages)}
    return Response(data, status=response.status_code, headers=headers)

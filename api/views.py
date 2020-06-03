from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.sites.shortcuts import get_current_site
from django.utils.timezone import now
from preferences import preferences
from rest_framework import authentication, generics, mixins, serializers, viewsets
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from bikesharing.models import Bike, Location, LocationTracker, Rent, Station

from .serializers import (
    BikeSerializer,
    LocationTrackerUpdateSerializer,
    RentSerializer,
    SocialAppSerializer,
    StationSerializer,
)

# Create your views here.
# ViewSets define the view behavior.


class BikeViewSet(viewsets.ModelViewSet):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class CanRentBikePermission(BasePermission):
    """The request is authenticated as a user and has add_rent permission."""

    message = "You cannot rent a bike at this time."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.has_perm("bikesharing.add_rent")


"""
Returns current running Rents of the requesting user
"""


@authentication_classes([authentication.TokenAuthentication])
@permission_classes([IsAuthenticated])
class CurrentRentViewSet(
    viewsets.ModelViewSet, mixins.ListModelMixin, generics.GenericAPIView
):
    serializer_class = RentSerializer

    def get_queryset(self):
        user = self.request.user
        return Rent.objects.filter(user=user, rent_end=None)


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
        loc = Location.objects.create(source="TR")
        if tracker.bike:
            loc.bike = tracker.bike
        loc.geo = Point(float(lng), float(lat), srid=4326)
        loc.reported_at = now()
        loc.tracker = tracker
        if accuracy:
            loc.accuracy = accuracy
        loc.save()

    if tracker.bike:
        bike = tracker.bike
        bike.last_reported = now()

        if loc:
            # check if bike is near station and assign it to that station
            # distance ist configured in prefernces
            max_distance = preferences.BikeSharePreferences.station_match_max_distance
            station_closer_than_Xm = Station.objects.filter(
                location__distance_lte=(loc.geo, D(m=max_distance)), status="AC"
            ).first()
            if station_closer_than_Xm:
                bike.current_station = station_closer_than_Xm
            else:
                bike.current_station = None

        bike.save()

    if not loc:
        return Response({"success": True, "warning": "lat/lng missing"})

    return Response({"success": True})


@authentication_classes([authentication.TokenAuthentication])
@api_view(["POST"])
@permission_classes([IsAuthenticated, CanRentBikePermission])
def start_rent(request):
    bike_number = request.data.get("bike_number")
    # station = request.data.get("station")
    lat = request.data.get("lat")
    lng = request.data.get("lng")
    if not (bike_number):
        return Response({"error": "bike_number missing"}, status=400)
    # if (not lat or not lng) and (not station):
    #    return Response({"error": "lat and lng or station required"}, status=400)

    try:
        bike = Bike.objects.get(bike_number=bike_number)
    except Bike.DoesNotExist:
        return Response({"error": "bike does not exist"}, status=404)

    # #TODO: message for bikes who are lost
    # if (bike.state == 'MI'):
    #     errortext = """We miss this bike.
    #       Please bring it to the bike tent at the Open Village"""
    #     if (bike.lock):
    #         if (bike.lock.lock_type == "CL" and bike.lock.unlock_key):
    #             errortext = """We miss this bike.
    #               Please bring it to the bike tent at the Open Village.
    #               Unlock key is """ + bike.lock.unlock_key
    #
    #     return Response({"error": errortext}, status=400)

    # check bike availability and set status to "in use"
    if bike.availability_status != "AV":
        return Response({"error": "bike is not available"}, status=409)
    bike.availability_status = "IU"
    bike.save()

    rent = Rent.objects.create(rent_start=now(), user=request.user, bike=bike)
    if lat and lng:
        rent.start_position = Point(float(lng), float(lat), srid=4326)

        loc = Location.objects.create(bike=bike, source="US")
        loc.geo = Point(float(lng), float(lat), srid=4326)
        loc.reported_at = now()
        loc.save()
    else:
        if bike.public_geolocation():
            rent.start_position = bike.public_geolocation().geo
    rent.save()
    # TODO station position and bike position if no lat lng over APIt

    res = {"success": True}
    # TODO return Lock code (or Open Lock?)
    if bike.lock:
        if bike.lock.lock_type == "CL" and bike.lock.unlock_key:
            res["unlock_key"] = bike.lock.unlock_key

    return Response(res)


@authentication_classes([authentication.TokenAuthentication])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def finish_rent(request):
    lat = request.data.get("lat")
    lng = request.data.get("lng")
    rent_id = request.data.get("rent_id")
    try:
        rent = Rent.objects.get(id=rent_id)
    except Rent.DoesNotExist:
        return Response({"error": "rent does not exist"}, status=404)

    if rent.user != request.user:
        return Response({"error": "rent belongs to another user"}, status=403)
    if rent.rent_end is not None:
        return Response({"error": "rent was already finished"}, status=410)

    rent.rent_end = now()
    if lat and lng:
        rent.end_position = Point(float(lng), float(lat), srid=4326)

        loc = Location.objects.create(bike=rent.bike, source="US")
        loc.geo = Point(float(lng), float(lat), srid=4326)
        loc.reported_at = now()
        loc.save()
    else:
        if rent.bike.public_geolocation():
            rent.end_position = rent.bike.public_geolocation().geo
    rent.save()

    if rent.end_position:
        # attach bike to station if location is closer than X meters
        # distance is configured in preferences
        max_distance = preferences.BikeSharePreferences.station_match_max_distance
        station_closer_than_Xm = Station.objects.filter(
            location__distance_lte=(rent.end_position, D(m=max_distance)), status="AC"
        ).first()
        if station_closer_than_Xm:
            rent.bike.current_station = station_closer_than_Xm
        else:
            rent.bike.current_station = None

    # set Bike status back to available
    rent.bike.availability_status = "AV"
    rent.bike.save()

    return Response({"success": True})


class UserDetailsSerializer(serializers.ModelSerializer):
    """User model w/o password."""

    can_rent_bike = serializers.SerializerMethodField()

    def get_can_rent_bike(self, user):
        return user.has_perm("bikesharing.add_rent")

    class Meta:
        model = get_user_model()
        fields = ("pk", "username", "can_rent_bike")


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


"""
return the configured social login providers
"""


@permission_classes([AllowAny])
class LoginProviderViewSet(
    viewsets.ModelViewSet, mixins.ListModelMixin, generics.GenericAPIView
):
    serializer_class = SocialAppSerializer

    def get_queryset(self):
        return SocialApp.objects.filter(sites__id=get_current_site(self.request).id)

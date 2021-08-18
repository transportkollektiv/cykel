from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils.timezone import now, timedelta
from django.shortcuts import get_object_or_404
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
from cykel.models import CykelLogEntry

from .authentication import BasicTokenAuthentication
from .serializers import (
    BikeSerializer,
    CreateRentSerializer,
    LocationTrackerUpdateSerializer,
    MaintenanceBikeSerializer,
    RentSerializer,
    SocialAppSerializer,
    StationSerializer,
    UserDetailsSerializer,
    ReservationSerializer,
)

from schedule.models import Event

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
                bike=rent.bike,
                source=Location.Source.USER,
                reported_at=now(),
                geo=Point(float(lng), float(lat), srid=4326),
            )

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
        loc = Location(
            source=Location.Source.TRACKER,
            reported_at=now(),
            tracker=tracker,
            geo=Point(float(lng), float(lat), srid=4326),
        )
        if tracker.bike:
            loc.bike = tracker.bike
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

    someminutesago = now() - timedelta(minutes=15)
    data = {}
    if loc:
        data = {"location_id": loc.id}

    if tracker.tracker_status == LocationTracker.Status.MISSING:
        action_type = "cykel.tracker.missing_reporting"
        CykelLogEntry.create_unless_time(
            someminutesago, content_object=tracker, action_type=action_type, data=data
        )

    if tracker.bike and tracker.bike.state == Bike.State.MISSING:
        action_type = "cykel.bike.missing_reporting"
        CykelLogEntry.create_unless_time(
            someminutesago,
            content_object=tracker.bike,
            action_type=action_type,
            data=data,
        )

    if not loc:
        return Response({"success": True, "warning": "lat/lng missing"})

    return Response({"success": True})


@authentication_classes(
    [SessionAuthentication, TokenAuthentication, BasicTokenAuthentication]
)
@permission_classes([IsAuthenticated, CanUseMaintenancePermission])
class MaintenanceViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["GET"])
    def mapdata(self, request):
        bikes = Bike.objects.filter(location__isnull=False).distinct()
        serializer = MaintenanceBikeSerializer(bikes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"])
    def logentryfeed(self, request):
        feed = LogEntryFeed()
        return feed(request)


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


class RSS20PaginatedFeed(Rss201rev2Feed):
    def add_root_elements(self, handler):
        super(Rss201rev2Feed, self).add_root_elements(handler)

        if self.feed["page"] > 1:
            handler.addQuickElement(
                "link",
                "",
                {
                    "rel": "first",
                    "href": self.feed["feed_url"],
                },
            )

        if self.feed["page"] < self.feed["last_page"]:
            handler.addQuickElement(
                "link",
                "",
                {
                    "rel": "last",
                    "href": (f"{self.feed['feed_url']}?page={self.feed['last_page']}"),
                },
            )

        if self.feed["page"] > 1:
            handler.addQuickElement(
                "link",
                "",
                {
                    "rel": "previous",
                    "href": (f"{self.feed['feed_url']}?page={self.feed['page'] - 1}"),
                },
            )

        if self.feed["page"] < self.feed["last_page"]:
            handler.addQuickElement(
                "link",
                "",
                {
                    "rel": "next",
                    "href": (f"{self.feed['feed_url']}?page={self.feed['page'] + 1}"),
                },
            )


class LogEntryFeed(Feed):
    feed_type = RSS20PaginatedFeed

    def title(self):
        return f"Maintenance Events of {preferences.BikeSharePreferences.system_name}"

    def description(self):
        return self.title()

    def link(self):
        return reverse(
            "admin:%s_%s_changelist"
            % (CykelLogEntry._meta.app_label, CykelLogEntry._meta.model_name)
        )

    def get_object(self, request):
        page = int(request.GET.get("page", 1))
        entries = CykelLogEntry.objects.order_by("-timestamp").all()
        paginator = Paginator(entries, 25)
        return {"page": page, "paginator": paginator}

    def items(self, obj):
        return obj["paginator"].get_page(obj["page"])

    def feed_extra_kwargs(self, obj):
        context = super().feed_extra_kwargs(obj)
        context["page"] = obj["page"]
        context["last_page"] = obj["paginator"].num_pages
        return context

    def item_title(self, item):
        return item.display()

    def item_pubdate(self, item):
        return item.timestamp

    def item_updateddate(self, item):
        return item.timestamp

    def item_description(self, item):
        return self.item_title(item)

    def item_link(self, item):
        return reverse(
            "admin:%s_%s_change" % (item._meta.app_label, item._meta.model_name),
            args=[item.id],
        )


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

#@permission_classes([IsAuthenticated, CanRentBikePermission])
class ReservationViewSet(viewsets.ViewSet):
    def get_queryset(self):
        user = self.request.user
        return Event.objects.filter(creator = user)

    def list(self, request):
        queryset = self.get_queryset()
        serializer = ReservationSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        event = get_object_or_404(queryset, pk=pk)
        serializer = ReservationSerializer(event)
        return Response(serializer.data)

    def create(self, request):
        pass



# @api_view(["POST"])
# @permission_classes([HasAPIKey])
# def createReservation(request):
#     startDate = request.data.get("startDate")
#     endDate = request.data.get("endDate")
#     startStation = request.data.get("startStation")
#     data = {
#         'title': 'Reservation',
#         'start': '',
#         'end': '',
#     }
#     reservation = Event(**data)
#     reservation.create_relation(user, 'owner')

#     if not loc:
#         return Response({"success": True, "warning": "lat/lng missing"})

#     return Response({"success": True})
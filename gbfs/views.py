import time
from datetime import datetime, timedelta

import pytz
from django.http import JsonResponse
from preferences import preferences
from rest_framework import generics, mixins
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny

from bikesharing.models import Bike, Station

from .serializers import (
    GbfsFreeBikeStatusSerializer,
    GbfsStationInformationSerializer,
    GbfsStationStatusSerializer,
)


def gbfs(request):
    if request.method == "GET":
        data = {
            "en": {
                "feeds": [
                    {
                        "name": "system_information",
                        "url": getGbfsRoot(request) + "system_information.json",
                    },
                    {
                        "name": "station_information",
                        "url": getGbfsRoot(request) + "station_information.json",
                    },
                    {
                        "name": "station_status",
                        "url": getGbfsRoot(request) + "station_status.json",
                    },
                    {
                        "name": "free_bike_status",
                        "url": getGbfsRoot(request) + "free_bike_status.json",
                    },
                ]
            }
        }
        return JsonResponse(getGbfsWithData(data), safe=False)


def gbfsSystemInformation(request):
    if request.method == "GET":
        data = {"system_id": "TBD", "language": "TBD", "name": "TBD", "timezone": "TBD"}
        return JsonResponse(getGbfsWithData(data), safe=False)


@permission_classes([AllowAny])
class GbfsFreeBikeStatusViewSet(mixins.ListModelMixin, generics.GenericAPIView):
    serializer_class = GbfsFreeBikeStatusSerializer

    def get(self, request, *args, **kwargs):
        bsp = preferences.BikeSharePreferences
        # if configured filter vehicles, where time report
        # is older than configure allowed silent timepreiod
        if bsp.gbfs_hide_bikes_after_location_report_silence:
            bikes = Bike.objects.filter(
                availability_status="AV",
                last_reported__gte=datetime.now(pytz.utc)
                - timedelta(hours=bsp.gbfs_hide_bikes_after_location_report_hours),
                current_station=None,
                location__isnull=False,
            ).distinct()
        else:
            bikes = Bike.objects.filter(
                availability_status="AV", current_station=None, location__isnull=False
            ).distinct()
        serializer = GbfsFreeBikeStatusSerializer(bikes, many=True)
        bike_data = {"bikes": serializer.data}
        data = getGbfsWithData(bike_data)
        return JsonResponse(data, safe=False)


@permission_classes([AllowAny])
class GbfsStationInformationViewSet(mixins.ListModelMixin, generics.GenericAPIView):
    queryset = Station.objects.filter(status="AC")
    serializer_class = GbfsStationInformationSerializer

    def get(self, request, *args, **kwargs):
        stations = Station.objects.all()
        serializer = GbfsStationInformationSerializer(stations, many=True)
        station_data = {"stations": serializer.data}
        data = getGbfsWithData(station_data)
        return JsonResponse(data, safe=False)


@permission_classes([AllowAny])
class GbfsStationStatusViewSet(mixins.ListModelMixin, generics.GenericAPIView):
    queryset = Station.objects.filter(status="AC")
    serializer_class = GbfsStationStatusSerializer

    def get(self, request, *args, **kwargs):
        stations = Station.objects.filter(status="AC")
        serializer = GbfsStationStatusSerializer(stations, many=True)
        station_data = {"stations": serializer.data}
        data = getGbfsWithData(station_data)
        return JsonResponse(data, safe=False)


def getGbfsRoot(request):
    return request.scheme + "://" + request.get_host() + "/gbfs/"


def getGbfsWithData(data):
    return {"ttl": 0, "last_updated": int(time.time()), "data": data}

import time

from django.shortcuts import render
from rest_framework import routers, serializers, viewsets
from django.http import HttpResponse, JsonResponse

from .serializers import BikeSerializer
from .serializers import StationSerializer

from bikesharing.models import Bike
from bikesharing.models import Station

# Create your views here.
# ViewSets define the view behavior.
class BikeViewSet(viewsets.ModelViewSet):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer

class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer

def gbfs(request):
    if request.method == 'GET':
        data = {
            "en": {
                "feeds": [
                    {
                        "name": "system_information",
                        "url": getGbfsRoot(request) + "system_information.json"
                    },
                    {
                        "name": "station_information",
                        "url": getGbfsRoot(request) + "station_information.json"
                    },
                    {
                        "name": "station_status",
                        "url": getGbfsRoot(request) + "station_status.json"
                    },
                    {
                        "name": "free_bike_status",
                        "url": getGbfsRoot(request) + "free_bike_status.json"
                    }
                ]
            }
        }
        return JsonResponse(getGbfsWithData(data), safe=False)

def getGbfsRoot(request):
    return request.scheme + "://" + request.get_host() + "/gbfs/"

def getGbfsWithData(data):
    return {
        "ttl": 0,
        "last_updated": int(time.time()),
        "data": data
    }
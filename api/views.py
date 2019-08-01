import time

from django.shortcuts import render
from rest_framework import routers, serializers, viewsets, mixins, generics
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


def gbfsSystemInformation(request):
    if request.method == 'GET':
        data = {
            "system_id": "TBD",
            "language": "TBD",
            "name": "TBD",
            "timezone": "TBD"
        }
        return JsonResponse(getGbfsWithData(data), safe=False)

def gbfsFreeBikeStatus(request):
    if request.method == 'GET':
        bikes = Bike.objects.all()

        bikes = [x for x in bikes]
        data = {
            "bikes": bikes
        }
        return JsonResponse(getGbfsWithData(data), safe=False)
        
class GbfsFreeBikeStatusViewSet(mixins.ListModelMixin, generics.GenericAPIView):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer

    def get(self, request, *args, **kwargs):
        bikes = Bike.objects.all()
        serializer = BikeSerializer(bikes, many=True)
        data = getGbfsWithData(serializer.data)
        print(data)
        return JsonResponse(data, safe=False)


        """res = self.list(request, *args, **kwargs)
        print(res)
        return res"""


def getGbfsRoot(request):
    return request.scheme + "://" + request.get_host() + "/gbfs/"

def getGbfsWithData(data):
    return {
        "ttl": 0,
        "last_updated": int(time.time()),
        "data": data
    }
import time

from django.shortcuts import render
from rest_framework import routers, serializers, viewsets, mixins, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
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

@api_view(['POST'])
@permission_classes([AllowAny])
def updatebikelocation(request):
    #TODO: Auth für ttn service
    if request.method == 'POST':
        try:
            bike_number = request.data.get("bike_number")
            lat = request.data.get("lat")
            lng = request.data.get("lng")
            if not (bike_number):
                return JsonResponse({"error": "bike_number missing"})
            if not (lat):
                return JsonResponse({"error": "lat missing"})
            if not (lng):
                return JsonResponse({"error": "lng missing"})

            bike = Bike.objects.get(bike_number=bike_number)
            bike.current_position.x = lng
            bike.current_position.y = lat
            print(dir(bike))
            bike.save()
            
            return JsonResponse({"success": True})
        except Bike.DoesNotExist:
            return JsonResponse({"error": "bike does not exist"})
            
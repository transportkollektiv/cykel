import time
import datetime

from django.shortcuts import render
from rest_framework import routers, serializers, viewsets, mixins, generics
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import authentication
from django.http import HttpResponse, JsonResponse

from django.contrib.gis.geos import Point

from .serializers import BikeSerializer
from .serializers import StationSerializer
from .serializers import RentSerializer

from bikesharing.models import Bike
from bikesharing.models import Station
from bikesharing.models import Rent

# Create your views here.
# ViewSets define the view behavior.
class BikeViewSet(viewsets.ModelViewSet):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer

class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer

"""
Returns current running Rents of the requesting user
"""
@permission_classes([IsAuthenticated])
class CurrentRentViewSet(viewsets.ModelViewSet, mixins.ListModelMixin, generics.GenericAPIView):
    serializer_class = RentSerializer

    def get_queryset(self):
        user = self.request.user
        return Rent.objects.filter(user=user, rent_end=None)

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

@authentication_classes([authentication.BasicAuthentication])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_rent(request):
    #TODO: Auth für ttn service
    if request.method == 'POST':
        try:
            bike_number = request.data.get("bike_number")
            station = request.data.get("station")
            lat = request.data.get("lat")
            lng = request.data.get("lng")
            if not (bike_number):
                return JsonResponse({"error": "bike_number missing"})
            if (not lat or not lng) and (not station):
                return JsonResponse({"error": "lat and lng or station required"})

            #check bike availability and set status to "in use"
            bike = Bike.objects.get(bike_number=bike_number)
            if (bike.availability_status != 'AV'):
                return JsonResponse({"error": "bike is not available"})
            bike.availability_status = 'IU'
            bike.save()

            rent = Rent.objects.create(rent_start=datetime.datetime.now(), user=request.user, bike=bike)
            if (lat and lng):
                rent.start_position = Point(float(lng), float(lat), srid=4326)
                rent.save()
            #TODO station position and bike position if no lat lng over APIt
            
            res = {"success": True}
            #TODO return Lock code (or Open Lock?)
            if (bike.lock):
                if (bike.lock.lock_type == "CL" and bike.lock.unlock_key):
                    res["unlock_key"] = bike.lock.unlock_key

            return JsonResponse(res)
        except Bike.DoesNotExist:
            return JsonResponse({"error": "bike does not exist"})

@authentication_classes([authentication.BasicAuthentication])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_rent(request):
    #TODO: Auth für ttn service
    if request.method == 'POST':
        try:
            lat = request.data.get("lat")
            lng = request.data.get("lng")
            rent_id = request.data.get("rent_id")
            rent = Rent.objects.get(id=rent_id)
            if (rent.user != request.user):
                return JsonResponse({"error": "rent belongs to another user"})
            if (rent.rent_end!=None):
                return JsonResponse({"error": "rent was already finished"})

            rent.rent_end = datetime.datetime.now()
            if (lat and lng):
                rent.end_position = Point(float(lng), float(lat), srid=4326)
            rent.save()

            # set Bike status back to available
            rent.bike.availability_status = 'AV'
            rent.bike.save()

            return JsonResponse({"success": True})
        except Rent.DoesNotExist:
            return JsonResponse({"error": "rent does not exist"})


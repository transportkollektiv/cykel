import time
import datetime

from django.shortcuts import render
from django.contrib.gis.measure import D
from rest_framework import routers, serializers, viewsets, mixins, generics
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import authentication
from rest_framework_api_key.permissions import HasAPIKey
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from preferences import preferences

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
@authentication_classes([authentication.TokenAuthentication])
@permission_classes([IsAuthenticated])
class CurrentRentViewSet(viewsets.ModelViewSet, mixins.ListModelMixin, generics.GenericAPIView):
    serializer_class = RentSerializer

    def get_queryset(self):
        user = self.request.user
        return Rent.objects.filter(user=user, rent_end=None)

@api_view(['POST'])
@permission_classes([HasAPIKey])
def updatebikelocation(request):
    bike_number = request.data.get("bike_number")
    lat = request.data.get("lat")
    lng = request.data.get("lng")
    battery_voltage = request.data.get("battery_voltage")
    if not (bike_number):
        return JsonResponse({"error": "bike_number missing"})
    if not (lat):
        return JsonResponse({"error": "lat missing"})
    if not (lng):
        return JsonResponse({"error": "lng missing"})

    try:
        bike = Bike.objects.get(bike_number=bike_number)
    except Bike.DoesNotExist:
        return JsonResponse({"error": "bike does not exist"})

    bike.current_position = Point(float(lng), float(lat), srid=4326)
    bike.last_reported = datetime.datetime.now()
    if battery_voltage:
        bike.battery_voltage = battery_voltage

    #check if bike is near station and assign it to that station
    # distance ist configured in prefernces
    max_distance = preferences.BikeSharePreferences.station_match_max_distance
    station_closer_than_Xm = Station.objects.filter(
        location__distance_lte=(bike.current_position, D(m=max_distance)),
        status = 'AC'
    ).first()
    if station_closer_than_Xm:
        bike.current_station = station_closer_than_Xm
    else:
        bike.current_station = None

    bike.save()
    
    return JsonResponse({"success": True})

@authentication_classes([authentication.TokenAuthentication])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_rent(request):
    bike_number = request.data.get("bike_number")
    station = request.data.get("station")
    lat = request.data.get("lat")
    lng = request.data.get("lng")
    if not (bike_number):
        return JsonResponse({"error": "bike_number missing"})
    #if (not lat or not lng) and (not station):
    #    return JsonResponse({"error": "lat and lng or station required"})

    try:
            bike = Bike.objects.get(bike_number=bike_number)
    except Bike.DoesNotExist:
        return JsonResponse({"error": "bike does not exist"})

        """
        #TODO: message for bikes who are lost
        if (bike.state == 'MI'):
            errortext = "We miss this bike. Please bring it to the bike tent at the Open Village"
            if (bike.lock):
                if (bike.lock.lock_type == "CL" and bike.lock.unlock_key):
                    errortext = "We miss this bike. Please bring it to the bike tent at the Open Village. Unlock key is " + bike.lock.unlock_key
                    
            return JsonResponse({"error": errortext})
        """

        #check bike availability and set status to "in use"
        if (bike.availability_status != 'AV'):
            return JsonResponse({"error": "bike is not available"})
        bike.availability_status = 'IU'
        bike.save()

        rent = Rent.objects.create(rent_start=datetime.datetime.now(), user=request.user, bike=bike)
        if (lat and lng):
            rent.start_position = Point(float(lng), float(lat), srid=4326)
        else:
            rent.start_position = bike.current_position
        rent.save()
        #TODO station position and bike position if no lat lng over APIt
        
        res = {"success": True}
        #TODO return Lock code (or Open Lock?)
        if (bike.lock):
            if (bike.lock.lock_type == "CL" and bike.lock.unlock_key):
                res["unlock_key"] = bike.lock.unlock_key

        return JsonResponse(res)

@authentication_classes([authentication.TokenAuthentication])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_rent(request):
    lat = request.data.get("lat")
    lng = request.data.get("lng")
    rent_id = request.data.get("rent_id")
    try:
        rent = Rent.objects.get(id=rent_id)
    except Rent.DoesNotExist:
        return JsonResponse({"error": "rent does not exist"})

        if (rent.user != request.user):
            return JsonResponse({"error": "rent belongs to another user"})
        if (rent.rent_end!=None):
            return JsonResponse({"error": "rent was already finished"})

        rent.rent_end = datetime.datetime.now()
        if (lat and lng):
            rent.end_position = Point(float(lng), float(lat), srid=4326)
            rent.bike.current_position = Point(float(lng), float(lat), srid=4326)
        else:
            rent.end_position = rent.bike.current_position
        rent.save()

        # attach bike to station is location is closer than X meters
        # distance ist configured in prefernces
        max_distance = preferences.BikeSharePreferences.station_match_max_distance
        station_closer_than_Xm = Station.objects.filter(
            location__distance_lte=(rent.end_position, D(m=max_distance)),
            status = 'AC'
        ).first()
        if station_closer_than_Xm:
            rent.bike.current_station = station_closer_than_Xm
        else:
            rent.bike.current_station = None

        # set Bike status back to available
        rent.bike.availability_status = 'AV'
        rent.bike.save()

        return JsonResponse({"success": True})

class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    class Meta:
        model = get_user_model()
        fields = ('pk', 'username')

class UserDetailsView(generics.RetrieveAPIView):
    """
    Reads UserModel fields
    Accepts GET method.
    Default accepted fields: username
    Default display fields: pk, username
    Read-only fields: pk
    Returns UserModel fields.
    """
    serializer_class = UserDetailsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        """
        Adding this method since it is sometimes called when using
        django-rest-swagger
        https://github.com/Tivix/django-rest-auth/issues/275
        """
        return get_user_model().objects.none()

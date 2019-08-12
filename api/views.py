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


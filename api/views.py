from django.shortcuts import render
from rest_framework import routers, serializers, viewsets

from .serializers import BikeSerializer

from bikesharing.models import Bike

# Create your views here.
# ViewSets define the view behavior.
class BikeViewSet(viewsets.ModelViewSet):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
from rest_framework import routers, serializers, viewsets

from bikesharing.models import Bike
from bikesharing.models import Lock

# Serializers define the API representation.
class LockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Lock
        fields = ('mac_address',)

# Serializers define the API representation.
class BikeSerializer(serializers.HyperlinkedModelSerializer):
    lock = LockSerializer()

    class Meta:
        model = Bike
        fields = ('bike_number', 'lock')
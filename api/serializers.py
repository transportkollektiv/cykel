from django.utils.timezone import now
from rest_framework import routers, serializers, viewsets

from bikesharing.models import Bike
from bikesharing.models import Lock
from bikesharing.models import Station
from bikesharing.models import Rent
from bikesharing.models import LocationTracker

from allauth.socialaccount.models import SocialApp

from django.contrib.sites.models import Site

# class LocationSerializer(serializers.HyperlinkedModelSerializer):
#    class Meta:


# Serializers define the API representation.
class LockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Lock
        fields = ('mac_address', 'unlock_key', 'lock_type')

# Serializers define the API representation.


class BikeSerializer(serializers.HyperlinkedModelSerializer):
    lock = LockSerializer()

    class Meta:
        model = Bike
        fields = ('bike_number', 'lock',)


class StationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Station
        fields = ('station_name', 'location', 'max_bikes', 'status')


class RentSerializer(serializers.HyperlinkedModelSerializer):
    bike = BikeSerializer()

    class Meta:
        model = Rent
        fields = ('id', 'bike', 'rent_start',)

class SocialAppSerializer(serializers.HyperlinkedModelSerializer):
	auth_url = serializers.SerializerMethodField()

	def get_auth_url(self, object):
		request = self.context.get('request')
		return  request.scheme + "://" + request.get_host() +  "/auth/" + object.provider + "/login/"

	class Meta:
		model = SocialApp
		fields = ('provider', 'name', 'auth_url')

class LocationTrackerUpdateSerializer(serializers.ModelSerializer):
    lat = serializers.CharField(required=False)
    lng = serializers.CharField(required=False)
    accuracy = serializers.CharField(required=False)

    def save(self):
        self.instance.last_reported = now()
        super().save()

    def validate(self, data):
        if (data.get('lat') is None and data.get('lng') is not None) or (data.get('lat') is not None and data.get('lng') is None):
            raise serializers.ValidationError("lat and lng must be defined together")
        return data

    class Meta:
        model = LocationTracker
        fields = ('device_id', 'battery_voltage', 'lat', 'lng', 'accuracy')


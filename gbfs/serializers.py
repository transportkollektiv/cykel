import pytz

from datetime import datetime, timedelta

from rest_framework import routers, serializers, viewsets

from bikesharing.models import Bike
from bikesharing.models import Lock
from bikesharing.models import Station

class GbfsFreeBikeStatusSerializer(serializers.HyperlinkedModelSerializer):
	bike_id = serializers.CharField(source='bike_number', read_only=True)

	class Meta:
		model = Bike
		fields = ('bike_id', )

	def to_representation(self, instance):
		representation = super().to_representation(instance)
		representation['is_reserved'] = False #Default to False TODO: maybe configuration later
		representation['is_disabled'] = False #Default to False TODO: maybe configuration later
		if instance.current_position is not None and instance.current_position.x and instance.current_position.y:
			representation['lat'] = instance.current_position.y
			representation['lon'] = instance.current_position.x
		return representation

class GbfsStationInformationSerializer(serializers.HyperlinkedModelSerializer):
	name = serializers.CharField(source='station_name', read_only=True)
	capacity = serializers.IntegerField(source='max_bikes', read_only=True)
	station_id = serializers.CharField(source='id', read_only=True)

	class Meta:
		model = Station
		fields = ('name', 'capacity', 'station_id', )

	def to_representation(self, instance):
		representation = super().to_representation(instance)
		if instance.location is not None and instance.location.x and instance.location.y:
			representation['lat'] = instance.location.y
			representation['lon'] = instance.location.x
		return representation

class GbfsStationStatusSerializer(serializers.HyperlinkedModelSerializer):
	station_id = serializers.CharField(source='id', read_only=True)

	class Meta:
		model = Station
		fields = ('station_id', )

	def to_representation(self, instance):
		representation = super().to_representation(instance)
		representation['num_bikes_available'] = instance.bike_set.filter(availability_status='AV', last_reported__gte=datetime.now(pytz.utc) - timedelta(hours=1)).count()
		representation['num_docks_available'] = instance.max_bikes - representation['num_bikes_available']
		status = (instance.status == "AC") or False
		representation['is_installed'] = status
		representation['is_renting'] = status
		representation['is_returning'] = status
		return representation

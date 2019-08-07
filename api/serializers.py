from rest_framework import routers, serializers, viewsets

from bikesharing.models import Bike
from bikesharing.models import Lock
from bikesharing.models import Station

#class LocationSerializer(serializers.HyperlinkedModelSerializer):
#	class Meta:


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
        fields = ('bike_number', 'lock', 'current_position',)

class StationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Station
        fields = ('station_name','location', 'max_bikes', 'status')

class GbfsFreeBikeStatusSerialzer(serializers.HyperlinkedModelSerializer):
	bike_id = serializers.CharField(source='bike_number', read_only=True)

	class Meta:
		model = Bike
		fields = ('bike_id', 'current_position', )

	def to_representation(self, instance):
		print (dir(instance.current_position))
		print(instance.current_position.x)
		#print (vars(instance.current_position.x))
		ret = super().to_representation(instance)
		ret['is_reserved'] = False #Default to False TODO: maybe configuration later
		ret['is_disabled'] = False #Default to False TODO: maybe configuration later
		ret['additional_field'] = "lololol"
		if (instance.current_position.x and instance.current_position.y):
			ret['lat'] = instance.current_position.y
			ret['lon'] = instance.current_position.x
		return ret
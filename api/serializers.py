from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework import serializers

from bikesharing.models import Bike, LocationTracker, Lock, Rent, Station

# class LocationSerializer(serializers.HyperlinkedModelSerializer):
#    class Meta:


class LockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Lock
        fields = ("mac_address", "unlock_key", "lock_type")


class BikeSerializer(serializers.HyperlinkedModelSerializer):
    lock = LockSerializer()

    class Meta:
        model = Bike
        fields = (
            "bike_number",
            "lock",
        )


class StationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Station
        fields = ("station_name", "location", "max_bikes", "status")


class RentSerializer(serializers.HyperlinkedModelSerializer):
    bike = BikeSerializer()

    class Meta:
        model = Rent
        fields = (
            "id",
            "bike",
            "rent_start",
        )


class SocialAppSerializer(serializers.HyperlinkedModelSerializer):
    auth_url = serializers.SerializerMethodField()

    def get_auth_url(self, object):
        request = self.context.get("request")
        return (
            request.scheme
            + "://"
            + request.get_host()
            + "/auth/"
            + object.provider
            + "/login/"
        )

    class Meta:
        model = SocialApp
        fields = ("provider", "name", "auth_url")


class LocationTrackerUpdateSerializer(serializers.ModelSerializer):
    lat = serializers.CharField(required=False)
    lng = serializers.CharField(required=False)
    accuracy = serializers.CharField(required=False)

    def save(self):
        self.instance.last_reported = now()
        super().save()

    def validate(self, data):
        if (data.get("lat") is None and data.get("lng") is not None) or (
            data.get("lat") is not None and data.get("lng") is None
        ):
            raise serializers.ValidationError("lat and lng must be defined together")
        return data

    class Meta:
        model = LocationTracker
        fields = ("device_id", "battery_voltage", "lat", "lng", "accuracy")


class UserDetailsSerializer(serializers.ModelSerializer):
    """User model w/o password."""

    can_rent_bike = serializers.SerializerMethodField()

    def get_can_rent_bike(self, user):
        return user.has_perm("bikesharing.add_rent")

    class Meta:
        model = get_user_model()
        fields = ("pk", "username", "can_rent_bike")

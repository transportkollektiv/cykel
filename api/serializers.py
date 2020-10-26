from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils.timezone import now
from rest_framework import serializers

from bikesharing.models import (
    Bike,
    Location,
    LocationTracker,
    Lock,
    LockType,
    Rent,
    Station,
)


class LockTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LockType
        fields = ("name",)


class LockSerializer(serializers.HyperlinkedModelSerializer):
    form_factor = serializers.ReadOnlyField(source="lock_type.form_factor")

    class Meta:
        model = Lock
        fields = ("unlock_key", "form_factor")


class BikeSerializer(serializers.HyperlinkedModelSerializer):
    lock_type = serializers.ReadOnlyField(source="lock.lock_type.form_factor")

    class Meta:
        model = Bike
        fields = ("bike_number", "lock_type")


class StationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Station
        fields = ("station_name", "location", "max_bikes", "status")


class CreateRentSerializer(serializers.HyperlinkedModelSerializer):
    bike = serializers.SlugRelatedField(
        slug_field="bike_number", queryset=Bike.objects.all(), required=True
    )
    lat = serializers.CharField(required=False, write_only=True)
    lng = serializers.CharField(required=False, write_only=True)
    rent_start = serializers.DateTimeField(default=serializers.CreateOnlyDefault(now))
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Rent
        fields = ["id", "bike", "lat", "lng", "rent_start", "user"]
        extra_kwargs = {
            "lat": {"write_only": True},
            "lng": {"write_only": True},
            "user": {"write_only": True},
        }

    def create(self, validated_data):
        # drop lat/lng before building rent object
        data = validated_data
        data.pop("lat", None)
        data.pop("lng", None)
        return Rent.objects.create(**data)

    def save(self, **kwargs):
        super().save(**kwargs)
        # FIXME: This method contains too much self.instance. doesn't feel good.
        # Should this stuff go into the model?
        self.instance.bike.availability_status = "IU"
        self.instance.bike.save()

        if (
            self.validated_data.get("lat") is not None
            and self.validated_data.get("lng") is not None
        ):
            pos = Point(
                float(self.validated_data.get("lng")),
                float(self.validated_data.get("lat")),
                srid=4326,
            )
            self.instance.start_position = pos

            loc = Location.objects.create(
                bike=self.instance.bike, source="US", reported_at=now()
            )
            loc.geo = pos
            loc.save()
        else:
            if self.instance.bike.public_geolocation():
                self.instance.start_position = (
                    self.instance.bike.public_geolocation().geo
                )
            if self.instance.bike.current_station:
                self.instance.start_station = self.instance.bike.current_station

        self.instance.save()

    def validate_bike(self, value):
        # seems there is no way to get the already validated and expanded bike obj
        bike = Bike.objects.get(bike_number=value)
        if bike.availability_status != "AV":
            raise serializers.ValidationError("bike is not available")
        return value

    def validate(self, data):
        if (data.get("lat") is None and data.get("lng") is not None) or (
            data.get("lat") is not None and data.get("lng") is None
        ):
            raise serializers.ValidationError("lat and lng must be defined together")
        return data


class RentSerializer(serializers.HyperlinkedModelSerializer):
    bike = BikeSerializer(read_only=True)

    finish_url = serializers.HyperlinkedIdentityField(view_name="rent-finish")
    unlock_url = serializers.HyperlinkedIdentityField(view_name="rent-unlock")

    class Meta:
        model = Rent
        fields = ["url", "id", "bike", "rent_start", "finish_url", "unlock_url"]


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


class MaintenanceBikeSerializer(serializers.ModelSerializer):
    bike_id = serializers.CharField(source="non_static_bike_uuid", read_only=True)

    class Meta:
        model = Bike
        fields = (
            "bike_id",
            "bike_number",
            "state",
            "availability_status",
            "internal_note",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        trackerserializer = MaintenanceTrackerSerializer(
            instance.locationtracker_set.all(), many=True
        )
        representation["trackers"] = trackerserializer.data
        lockserializer = MaintenanceLockSerializer(instance.lock)
        representation["lock"] = lockserializer.data

        public_geolocation = instance.public_geolocation()
        if public_geolocation is not None:
            pos = public_geolocation.geo
            if pos and pos.x and pos.y:
                representation["lat"] = pos.y
                representation["lng"] = pos.x
        return representation  # only return bikes with public geolocation


class MaintenanceTrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationTracker
        fields = (
            "device_id",
            "battery_voltage",
            "internal",
            "last_reported",
            "tracker_type",
            "tracker_status",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        current_location = instance.current_geolocation()
        if current_location:
            representation["last_location_reported"] = current_location.reported_at
            current_geolocation = current_location.geo
            if current_geolocation and current_geolocation.x and current_geolocation.y:
                representation["lat"] = current_geolocation.y
                representation["lng"] = current_geolocation.x
        return representation


class MaintenanceLockTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LockType
        fields = ("name",)


class MaintenanceLockSerializer(serializers.ModelSerializer):
    lock_type = MaintenanceLockTypeSerializer()

    class Meta:
        model = Lock
        fields = ("unlock_key", "lock_type", "lock_id")

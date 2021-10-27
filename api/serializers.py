from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils.timezone import now, timedelta
from rest_framework import serializers
from schedule.models import Event

from bikesharing.models import (
    Bike,
    Location,
    LocationTracker,
    LocationTrackerType,
    Lock,
    LockType,
    Rent,
    Station,
    VehicleType,
)
from cykel.models import CykelLogEntry
from cykel.serializers import MappedChoiceField
from reservation.models import Reservation


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


class VehicleTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VehicleType
        fields = ("name",)


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
        bike = self.validated_data["bike"]
        if (
            self.validated_data.get("lat") is not None
            and self.validated_data.get("lng") is not None
        ):
            pos = Point(
                float(self.validated_data["lng"]),
                float(self.validated_data["lat"]),
                srid=4326,
            )

            loc = Location.objects.create(
                bike=bike,
                source=Location.Source.USER,
                reported_at=now(),
                geo=pos,
            )
            self.validated_data["start_location"] = loc
        else:
            if bike.public_geolocation():
                self.validated_data["start_location"] = bike.public_geolocation()
            if bike.current_station:
                self.validated_data["start_station"] = bike.current_station

        super().save(**kwargs)

        bike.availability_status = Bike.Availability.IN_USE
        bike.save()

    def validate_bike(self, value):
        # seems there is no way to get the already validated and expanded bike obj
        bike = Bike.objects.get(bike_number=value)
        if bike.availability_status != Bike.Availability.AVAILABLE:
            raise serializers.ValidationError("bike is not available")
        if not bike.vehicle_type.allow_spontaneous_rent:
            raise serializers.ValidationError(
                "bike is not allowed for spontaneous rents"
            )
        if bike.vehicle_type.allow_reservation:
            available_bikes = Bike.objects.filter(
                vehicle_type=bike.vehicle_type, state=Bike.Availability.AVAILABLE
            )
            if len(available_bikes) - bike.vehicle_type.min_reservation_vehicles < 1:
                raise serializers.ValidationError("bike is reserved")
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

        if (
            self.instance.tracker_status == LocationTracker.Status.ACTIVE
            and self.instance.battery_voltage is not None
            and self.instance.tracker_type is not None
        ):
            data = {"voltage": self.instance.battery_voltage}
            action_type = None
            action_type_prefix = "cykel.tracker"

            if self.instance.bike:
                data["bike_id"] = self.instance.bike.pk
                action_type_prefix = "cykel.bike.tracker"

            if (
                self.instance.tracker_type.battery_voltage_critical is not None
                and self.instance.battery_voltage
                <= self.instance.tracker_type.battery_voltage_critical
            ):
                action_type = "battery.critical"
            elif (
                self.instance.tracker_type.battery_voltage_warning is not None
                and self.instance.battery_voltage
                <= self.instance.tracker_type.battery_voltage_warning
            ):
                action_type = "battery.warning"

            if action_type is not None:
                action_type = "{}.{}".format(action_type_prefix, action_type)
                somehoursago = now() - timedelta(hours=48)
                CykelLogEntry.create_unless_time(
                    somehoursago,
                    content_object=self.instance,
                    action_type=action_type,
                    data=data,
                )

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
    availability_status = MappedChoiceField(choices=Bike.Availability)
    state = MappedChoiceField(choices=Bike.State)

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


class MaintenanceTrackerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationTrackerType
        fields = ("name", "battery_voltage_warning", "battery_voltage_critical")


class MaintenanceTrackerSerializer(serializers.ModelSerializer):
    tracker_status = MappedChoiceField(choices=LocationTracker.Status)
    tracker_type = MaintenanceTrackerTypeSerializer()

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
    form_factor = MappedChoiceField(choices=LockType.FormFactor)

    class Meta:
        model = LockType
        fields = ("name", "form_factor")


class MaintenanceLockSerializer(serializers.ModelSerializer):
    lock_type = MaintenanceLockTypeSerializer()

    class Meta:
        model = Lock
        fields = ("unlock_key", "lock_type", "lock_id")


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("id", "start", "end", "creator")


class ReservationSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    start_location = StationSerializer(read_only=True)
    bike = BikeSerializer(read_only=True)
    vehicle_type = VehicleTypeSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = ("id", "start_location", "event", "bike", "vehicle_type", "rent")

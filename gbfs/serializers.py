from datetime import timedelta

from django.utils.timezone import now
from preferences import preferences
from rest_framework import fields, serializers

from bikesharing.models import Bike, Station, VehicleType
from cykel.serializers import EnumFieldSerializer


class TimestampSerializer(fields.CharField):
    def to_representation(self, value):
        return value.timestamp()


class GbfsFreeBikeStatusSerializer(serializers.HyperlinkedModelSerializer):
    bike_id = serializers.CharField(source="non_static_bike_uuid", read_only=True)
    vehicle_type_id = serializers.CharField(read_only=True)
    last_reported = TimestampSerializer(read_only=True)

    class Meta:
        model = Bike
        fields = (
            "bike_id",
            "vehicle_type_id",
            "current_range_meters",
            "last_reported",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # defined by GBFS 2.1: Only if the vehicle has a motor the field is required
        if (
            instance.vehicle_type is not None
            and instance.vehicle_type.propulsion_type
            == VehicleType.PropulsionType.HUMAN
        ):
            representation.pop("current_range_meters")
        # Default to False TODO: maybe configuration later
        representation["is_reserved"] = False
        # Default to False TODO: maybe configuration later
        representation["is_disabled"] = False
        public_geolocation = instance.public_geolocation()
        if public_geolocation is not None:
            pos = public_geolocation.geo
            if pos and pos.x and pos.y:
                representation["lat"] = pos.y
                representation["lon"] = pos.x
                return representation  # only return bikes with public geolocation


class GbfsVehicleOnStationSerializer(GbfsFreeBikeStatusSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation is None:
            return None
        representation.pop("lat")
        representation.pop("lon")
        return representation


class GbfsStationInformationSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(source="station_name", read_only=True)
    capacity = serializers.IntegerField(source="max_bikes", read_only=True)
    station_id = serializers.CharField(source="id", read_only=True)

    class Meta:
        model = Station
        fields = (
            "name",
            "capacity",
            "station_id",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if (
            instance.location is not None
            and instance.location.x
            and instance.location.y
        ):
            representation["lat"] = instance.location.y
            representation["lon"] = instance.location.x
        return representation


class GbfsStationStatusSerializer(serializers.HyperlinkedModelSerializer):
    station_id = serializers.CharField(source="id", read_only=True)
    vehicles = serializers.SerializerMethodField()

    def get_vehicles(self, obj):
        # if configured filter vehicles, where time report
        # is older than configure allowed silent timeperiod
        bsp = preferences.BikeSharePreferences
        if bsp.gbfs_hide_bikes_after_location_report_silence:
            available_bikes = obj.bike_set.filter(
                availability_status=Bike.Availability.AVAILABLE,
                last_reported__gte=now()
                - timedelta(hours=bsp.gbfs_hide_bikes_after_location_report_hours),
            )
        else:
            available_bikes = obj.bike_set.filter(
                availability_status=Bike.Availability.AVAILABLE
            )
        vehicles = GbfsVehicleOnStationSerializer(available_bikes, many=True).data
        return list(filter(lambda val: val is not None, vehicles))

    class Meta:
        model = Station
        fields = (
            "station_id",
            "vehicles",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["num_bikes_available"] = len(representation["vehicles"])
        representation["num_docks_available"] = (
            instance.max_bikes - representation["num_bikes_available"]
        )

        if representation["num_bikes_available"] > 0:
            representation["last_reported"] = max(
                (
                    vehicle["last_reported"]
                    if vehicle["last_reported"] is not None
                    else 0
                )
                for vehicle in representation["vehicles"]
            )
        else:
            # if no bike is at the station, last_report is the current time
            # not sure if this is the intended behavior of the field
            # or it should be the timestamp of the last bike removed
            # but it is not so easy to implement
            representation["last_reported"] = int(now().timestamp())

        def drop_last_reported(obj):
            obj.pop("last_reported")
            return obj

        representation["vehicles"] = list(
            map(drop_last_reported, representation["vehicles"])
        )

        status = (instance.status == Station.Status.ACTIVE) or False
        representation["is_installed"] = status
        representation["is_renting"] = status
        representation["is_returning"] = status
        return representation


class GbfsVehicleTypeSerializer(serializers.HyperlinkedModelSerializer):
    vehicle_type_id = serializers.CharField(source="id", read_only=True)
    allow_reservation = serializers.BooleanField(read_only=True)
    allow_spontaneous_rent = serializers.BooleanField(read_only=True)
    form_factor = EnumFieldSerializer(
        read_only=True,
        mapping={
            VehicleType.FormFactor.BIKE: "bicycle",
            VehicleType.FormFactor.ESCOOTER: "scooter",
            VehicleType.FormFactor.CAR: "car",
            VehicleType.FormFactor.MOPED: "moped",
            VehicleType.FormFactor.OTHER: "other",
        },
    )
    propulsion_type = EnumFieldSerializer(
        read_only=True,
        mapping={
            VehicleType.PropulsionType.HUMAN: "human",
            VehicleType.PropulsionType.ELECTRIC_ASSIST: "electric_assist",
            VehicleType.PropulsionType.ELECTRIC: "electric",
            VehicleType.PropulsionType.COMBUSTION: "combustion",
        },
    )

    def to_representation(self, instance):
        data = super(GbfsVehicleTypeSerializer, self).to_representation(instance)
        # defined by GBFS 2.1: Only if the vehicle has a motor the field is required
        if instance.propulsion_type == VehicleType.PropulsionType.HUMAN:
            data.pop("max_range_meters")
        return data

    class Meta:
        model = VehicleType
        fields = (
            "vehicle_type_id",
            "allow_reservation",
            "allow_spontaneous_rent",
            "form_factor",
            "propulsion_type",
            "max_range_meters",
            "name",
        )

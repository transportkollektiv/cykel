from datetime import timedelta

from django.db.models import Max
from django.utils.timezone import now
from preferences import preferences
from rest_framework import serializers

from bikesharing.models import Bike, Station


class GbfsFreeBikeStatusSerializer(serializers.HyperlinkedModelSerializer):
    bike_id = serializers.CharField(source="non_static_bike_uuid", read_only=True)

    class Meta:
        model = Bike
        fields = ("bike_id",)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
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
                return representation #only return bikes with public geolocation


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

    class Meta:
        model = Station
        fields = ("station_id",)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # if configured filter vehicles, where time report
        # is older than configure allowed silent timeperiod
        bsp = preferences.BikeSharePreferences
        if bsp.gbfs_hide_bikes_after_location_report_silence:
            available_bikes = instance.bike_set.filter(
                availability_status="AV",
                last_reported__gte=now()
                - timedelta(hours=bsp.gbfs_hide_bikes_after_location_report_hours),
            )
        else:
            available_bikes = instance.bike_set.filter(availability_status="AV")
        representation["num_bikes_available"] = available_bikes.count()
        representation["num_docks_available"] = (
            instance.max_bikes - representation["num_bikes_available"]
        )
        last_reported_bike = available_bikes.aggregate(Max("last_reported"))

        if last_reported_bike["last_reported__max"] is not None:
            representation["last_reported"] = int(
                last_reported_bike["last_reported__max"].timestamp()
            )
        else:
            # if no bike is on station, last_report is now
            # not shure if this is the intended behavior of the field
            # or it should be the timestamp of the last bike removed
            # but it is not so easy to implement
            representation["last_reported"] = int(now().timestamp())

        status = (instance.status == "AC") or False
        representation["is_installed"] = status
        representation["is_renting"] = status
        representation["is_returning"] = status
        return representation

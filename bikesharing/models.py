import uuid

from django.conf import settings
from django.contrib.gis.db import models as geomodels
from django.contrib.gis.measure import D
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.utils import IntegrityError
from django.utils.timezone import now
from macaddress.fields import MACAddressField
from preferences import preferences
from preferences.models import Preferences

bike_availability_status_choices = (
    ("DI", "Disabled"),
    ("IU", "In Use"),
    ("AV", "Available"),
)

bike_state_status_choices = (
    ("US", "Usable"),
    ("BR", "Broken"),
    ("IR", "In Repair"),
    ("MI", "Missing"),
)

bike_type_choices = (
    ("BI", "Bike"),
    ("CB", "Cargo Bike"),
    ("EB", "E-Bike"),
    ("ES", "E-Scooter"),
    ("WH", "Wheelchair"),
)

lock_type_choices = (
    ("CL", "Combination lock"),
    ("EL", "Electronic Lock"),
)

station_status_choices = (
    ("DI", "Disabled"),
    ("AC", "Active"),
)

location_source_choices = (("LO", "Lock"), ("TR", "Tracker"), ("US", "User"))

tracker_status_choices = (
    ("AC", "Active"),
    ("IN", "Inactive"),
    ("MI", "Missing"),
    ("DE", "Decommissioned"),
)


class Bike(models.Model):
    bike_number = models.CharField(max_length=8)
    availability_status = models.CharField(
        max_length=2, choices=bike_availability_status_choices, default="DI"
    )
    state = models.CharField(
        max_length=2, choices=bike_state_status_choices, default="US"
    )
    bike_type = models.CharField(max_length=2, choices=bike_type_choices, default="BI")
    lock = models.ForeignKey("Lock", on_delete=models.PROTECT, null=True, blank=True)
    current_station = models.ForeignKey(
        "Station", on_delete=models.PROTECT, blank=True, null=True, default=None
    )
    last_reported = models.DateTimeField(default=None, null=True, blank=True)
    internal_note = models.TextField(default=None, null=True, blank=True)
    photo = models.FileField(
        upload_to="uploads/", default=None, null=True, blank=True
    )  # TODO Thumbnail
    vehicle_identification_number = models.CharField(
        default=None, null=True, blank=True, max_length=17
    )
    non_static_bike_uuid = models.UUIDField(
        default=uuid.uuid4,
        blank=False,
        unique=True,
        help_text="""A temporary ID used in public APIs,
        rotating it's value after each rent to protect users privacy.""",
    )

    def __str__(self):
        return str(self.bike_number)

    def __repr__(self):
        return "#{bike_number} ({state}) @ {position} ({last_reported})".format(
            bike_number=self.bike_number,
            state=self.state,
            position=self.public_geolocation(),
            last_reported=self.last_reported,
        )

    def public_geolocation(self):
        if not self.id:
            return None
        try:
            return Location.objects.filter(bike=self, internal=False).latest(
                "reported_at"
            )
        except ObjectDoesNotExist:
            return None

    def internal_geolocation(self):
        if not self.id:
            return None
        try:
            return Location.objects.filter(bike=self, internal=True).latest(
                "reported_at"
            )
        except ObjectDoesNotExist:
            return None


class LocationTracker(models.Model):
    bike = models.ForeignKey("Bike", on_delete=models.PROTECT, null=True, blank=True)
    device_id = models.CharField(default=None, null=False, blank=True, max_length=255)
    last_reported = models.DateTimeField(default=None, null=True, blank=True)
    battery_voltage = models.FloatField(default=None, null=True, blank=True)
    tracker_type = models.CharField(default=None, null=True, blank=True, max_length=255)
    tracker_status = models.CharField(
        max_length=2, choices=tracker_status_choices, default="IN"
    )
    internal = models.BooleanField(
        default=False,
        help_text="""Internal trackers don't publish their locations to the enduser.
         They are useful for backup trackers with lower accuracy e.g. wifi trackers.""",
    )

    def current_geolocation(self):
        if not self.id:
            return None
        try:
            return Location.objects.filter(tracker=self).latest("reported_at")
        except ObjectDoesNotExist:
            return None

    def __str__(self):
        return str(self.device_id)


class Rent(models.Model):
    rent_start = models.DateTimeField()
    rent_end = models.DateTimeField(default=None, null=True, blank=True)
    start_position = geomodels.PointField(default=None, null=True)
    start_station = models.ForeignKey(
        "Station",
        default=None,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)s_start_station",
    )
    end_position = geomodels.PointField(default=None, null=True)
    end_station = models.ForeignKey(
        "Station",
        default=None,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)s_end_station",
    )
    bike = models.ForeignKey("Bike", default=None, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __repr__(self):
        return """Bike {bike} for User '{user}'\n  rented {rent_start}
            from {start_position}/{start_station}\n  return {rent_end}
            at {end_position}/{end_station}""".format(
            bike=self.bike,
            user=self.user,
            start_position=self.start_position,
            start_station=self.start_station,
            rent_start=self.rent_start,
            end_position=self.end_position,
            end_station=self.end_station,
            rent_end=self.rent_end,
        )

    def end(self, end_position=None):
        self.rent_end = now()
        if end_position is not None:
            self.end_position = end_position
        elif self.bike.public_geolocation():
            self.end_position = self.bike.public_geolocation().geo
        self.save()

        if self.end_position:
            # attach bike to station if location is closer than X meters
            # distance is configured in preferences
            max_distance = preferences.BikeSharePreferences.station_match_max_distance
            station_closer_than_Xm = Station.objects.filter(
                location__distance_lte=(self.end_position, D(m=max_distance)),
                status="AC",
            ).first()
            if station_closer_than_Xm:
                self.bike.current_station = station_closer_than_Xm
                self.end_station = station_closer_than_Xm
                self.save()
            else:
                self.bike.current_station = None

        # set Bike status back to available
        self.bike.availability_status = "AV"
        self.bike.save()
        try:
            # set new non static bike ID, so for GBFS observers can not track this bike
            self.bike.non_static_bike_uuid = uuid.uuid4()
            self.bike.save()
        except IntegrityError:
            # Congratulations! The 2^64 chance of uuid4 collision has happend.
            # here coul'd be the place for the famous comment: "should never happen"
            # So we catch this error here, but don't handle it.
            # because don't rotating a uuid every 18,446,744,073,709,551,615 rents is ok
            pass


class Lock(models.Model):
    lock_id = models.CharField(editable=True, max_length=255)
    lock_type = models.CharField(max_length=2, choices=lock_type_choices, default="CL")
    mac_address = MACAddressField(null=True, blank=True)
    unlock_key = models.CharField(editable=True, max_length=255, blank=True)

    def __str__(self):
        return "#{lock_id} ({lock_type})".format(
            lock_id=self.lock_id, lock_type=self.lock_type
        )

    def __repr__(self):
        return """#{lock_id} ({lock_type})
         mac_address={mac_address} unlock_key={unlock_key}""".format(
            lock_id=self.lock_id,
            lock_type=self.lock_type,
            mac_address=self.mac_address,
            unlock_key=self.unlock_key,
        )


class Station(models.Model):
    status = models.CharField(
        max_length=2, choices=station_status_choices, default="DI"
    )
    station_name = models.CharField(max_length=255)
    location = geomodels.PointField(default=None, null=True)
    max_bikes = models.IntegerField(default=10)

    def __str__(self):
        return self.station_name

    def __repr__(self):
        return "Station '{station_name}', max. {max_bikes} bikes ({location})".format(
            station_name=self.station_name,
            max_bikes=self.max_bikes,
            location=self.location,
        )


class BikeSharePreferences(Preferences):
    station_match_max_distance = models.IntegerField(default=20)
    gbfs_hide_bikes_after_location_report_silence = models.BooleanField(
        default=False,
        help_text="""If activated, vehicles will disappear from GBFS,
         if there was no location report in the configured time period.""",
    )
    gbfs_hide_bikes_after_location_report_hours = models.IntegerField(
        default=1,
        help_text="""Time period (in hours) after the vehicles will
         be hidden from GBFS, if there was no location report.
         Needs 'Gbfs hide bikes after location report silence' activated.""",
    )
    gbfs_system_id = models.CharField(editable=True, max_length=255, default="")
    system_name = models.CharField(editable=True, max_length=255, default="")
    system_short_name = models.CharField(editable=True, max_length=255, default="")


class Location(models.Model):
    bike = models.ForeignKey(
        "Bike", blank=True, null=True, default=None, on_delete=models.PROTECT
    )
    tracker = models.ForeignKey(
        "LocationTracker", null=True, default=None, on_delete=models.PROTECT
    )
    geo = geomodels.PointField(default=None, null=True, blank=True)
    source = models.CharField(
        max_length=2, choices=location_source_choices, default="LO"
    )
    reported_at = models.DateTimeField(default=None, null=True, blank=True)
    accuracy = models.FloatField(default=None, null=True, blank=True)
    internal = models.BooleanField(
        default=False,
        help_text="""Internal locations are not published to the enduser.
         They are useful for backup trackers with lower accuracy e.g. wifi trackers.""",
    )

    def save(self, *args, **kwargs):
        if self.tracker:
            self.internal = self.tracker.internal
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.geo)

    class Meta:
        get_latest_by = "reported_at"

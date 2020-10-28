import uuid
from textwrap import dedent

import requests
from django.conf import settings
from django.contrib.gis.db import models as geomodels
from django.contrib.gis.measure import D
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from preferences import preferences
from preferences.models import Preferences


class VehicleType(models.Model):
    class FormFactor(models.TextChoices):
        """These factors are defined by GBFS v2.1."""

        BIKE = "BI", _("Bike")
        ESCOOTER = "ES", _("E-Scooter")
        CAR = "CA", _("Car")
        MOPED = "MO", _("Moped")
        OTHER = "OT", _("Other")

    class PropulsionType(models.TextChoices):
        """These factors are defined by GBFS v2.1."""

        HUMAN = "HU", _("Human")
        ELECTRIC_ASSIST = "EA", _("Electric Assist")
        ELECTRIC = "EL", _("Electric")
        COMBUSTION = "CO", _("Combustion")

    name = models.CharField(default=None, null=True, blank=True, max_length=255)
    form_factor = models.CharField(
        max_length=2, choices=FormFactor.choices, default=FormFactor.BIKE
    )
    propulsion_type = models.CharField(
        max_length=2, choices=PropulsionType.choices, default=PropulsionType.HUMAN
    )
    max_range_meters = models.FloatField(
        default=None,
        null=True,
        blank=True,
        help_text=dedent(
            """\
            If the vehicle has a motor, the furthest distance in meters
            that the vehicle can travel without recharging or refueling
            when it has the maximum amount of energy potential
            (for example a full battery or full tank of gas)."""
        ),
    )  # TODO: validation only positive values
    internal_note = models.TextField(default=None, null=True, blank=True)

    def __str__(self):
        return str(self.name)


class Bike(models.Model):
    class Availability(models.TextChoices):
        DISABLED = "DI", _("Disabled")
        IN_USE = "IU", _("In Use")
        AVAILABLE = "AV", _("Available")

    class State(models.TextChoices):
        USABLE = "US", _("Usable")
        BROKEN = "BR", _("Broken")
        IN_REPAIR = "IR", _("In Repair")
        MISSING = "MI", _("Missing")

    bike_number = models.CharField(max_length=8)
    availability_status = models.CharField(
        max_length=2, choices=Availability.choices, default=Availability.DISABLED
    )
    state = models.CharField(max_length=2, choices=State.choices, default=State.USABLE)
    vehicle_type = models.ForeignKey(
        "VehicleType", on_delete=models.PROTECT, null=True, blank=True
    )
    lock = models.OneToOneField("Lock", on_delete=models.PROTECT, null=True, blank=True)
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
    current_range_meters = models.FloatField(
        default=None,
        null=True,
        blank=True,
        help_text=dedent(
            """\
            If the corresponding vehicle_type definition for this vehicle
            has a motor, then this field is required. This value represents
            the furthest distance in meters that the vehicle can travel
            without recharging or refueling with the vehicle's current
            charge or fuel.
            """
        ),
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
            return Location.objects.filter(
                bike=self, internal=False, reported_at__isnull=False
            ).latest("reported_at")
        except ObjectDoesNotExist:
            return None

    def internal_geolocation(self):
        if not self.id:
            return None
        try:
            return Location.objects.filter(
                bike=self, internal=True, reported_at__isnull=False
            ).latest("reported_at")
        except ObjectDoesNotExist:
            return None

    class Meta:
        permissions = [
            ("maintain", "Can use maintenance UI"),
        ]


class LocationTracker(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "AC", _("Active")
        INACTIVE = "IN", _("Inactive")
        MISSING = "MI", _("Missing")
        DECOMMISSIONED = "DE", _("Decommissioned")

    bike = models.ForeignKey("Bike", on_delete=models.PROTECT, null=True, blank=True)
    device_id = models.CharField(default=None, null=False, blank=True, max_length=255)
    last_reported = models.DateTimeField(default=None, null=True, blank=True)
    battery_voltage = models.FloatField(default=None, null=True, blank=True)
    tracker_type = models.CharField(default=None, null=True, blank=True, max_length=255)
    tracker_status = models.CharField(
        max_length=2, choices=Status.choices, default=Status.INACTIVE
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
            return Location.objects.filter(
                tracker=self, reported_at__isnull=False
            ).latest("reported_at")
        except ObjectDoesNotExist:
            return None

    def __str__(self):
        return str(self.device_id)


class LockType(models.Model):
    class FormFactor(models.TextChoices):
        COMBINATION_LOCK = "CL", _("Combination lock")
        ELECTRONIC_LOCK = "EL", _("Electronic Lock")

    name = models.CharField(default=None, null=True, blank=True, max_length=255)
    form_factor = models.CharField(
        max_length=2, choices=FormFactor.choices, default=FormFactor.COMBINATION_LOCK
    )
    endpoint_url = models.URLField(default=None, null=True, blank=True)

    def __str__(self):
        return str(self.name)


class Lock(models.Model):
    lock_id = models.CharField(editable=True, max_length=255)
    lock_type = models.ForeignKey(
        "LockType", on_delete=models.PROTECT, null=True, blank=True
    )
    unlock_key = models.CharField(editable=True, max_length=255, blank=True)

    def __str__(self):
        return "#{lock_id} ({lock_type})".format(
            lock_id=self.lock_id, lock_type=self.lock_type
        )

    def __repr__(self):
        return """#{lock_id} ({lock_type}) unlock_key={unlock_key}""".format(
            lock_id=self.lock_id,
            lock_type=self.lock_type,
            unlock_key=self.unlock_key,
        )


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

    def unlock(self):
        if self.bike.lock is None:
            return {}

        lock = self.bike.lock
        lock_type = lock.lock_type

        if lock_type is None:
            return {}

        if lock_type.form_factor == LockType.FormFactor.COMBINATION_LOCK:
            return {"unlock_key": self.bike.lock.unlock_key}

        if lock_type.form_factor == LockType.FormFactor.ELECTRONIC_LOCK:
            url = "{url}/{device_id}/unlock".format(
                url=lock_type.endpoint_url, device_id=lock.lock_id
            )
            r = requests.post(url)
            data = r.json()
            return {"data": data}

        return {}

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
                status=Station.Status.ACTIVE,
            ).first()
            if station_closer_than_Xm:
                self.bike.current_station = station_closer_than_Xm
                self.end_station = station_closer_than_Xm
                self.save()
            else:
                self.bike.current_station = None

        # set Bike status back to available
        self.bike.availability_status = Bike.Availability.AVAILABLE
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


class Station(models.Model):
    class Status(models.TextChoices):
        DISABLED = "DI", _("Disabled")
        ACTIVE = "AC", _("Active")

    status = models.CharField(
        max_length=2, choices=Status.choices, default=Status.DISABLED
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
    class Source(models.TextChoices):
        LOCK = "LO", _("Lock")
        TRACKER = "TR", _("Tracker")
        USER = "US", _("User")

    bike = models.ForeignKey(
        "Bike", blank=True, null=True, default=None, on_delete=models.PROTECT
    )
    tracker = models.ForeignKey(
        "LocationTracker", blank=True, null=True, default=None, on_delete=models.PROTECT
    )
    geo = geomodels.PointField(default=None, null=True, blank=True)
    source = models.CharField(max_length=2, choices=Source.choices, default=Source.LOCK)
    reported_at = models.DateTimeField(default=None, null=False, blank=False)
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

import uuid
from textwrap import dedent

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _

from .location import Location


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

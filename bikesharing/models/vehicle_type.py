from textwrap import dedent

from django.db import models
from django.utils.translation import gettext_lazy as _


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

    # fields used to handle reservations
    allow_spontaneous_rent = models.BooleanField(default=True)
    allow_reservation = models.BooleanField(default=False)
    min_spontaneous_rent_vehicles = models.IntegerField(
        default=0,
        help_text=dedent(
            """\
            Only used when reservations are allowed. Minimum number of vehicles that should be
            kept available for spontaneous rents."""
        ),
    )
    min_reservation_vehicles = models.IntegerField(
        default=0,
        help_text=dedent(
            """\
            Only used when reservations are allowed. Minimum number of vehicles that should be
            kept available for reservations."""
        ),
    )
    reservation_lead_time_minutes = models.IntegerField(
        default=120,
        help_text=dedent(
            """\
            Only used when reservations are allowed. Lead time in minutes to start the rent before the
            beginning of a reservation. This is to make sure that a vehicle is rented when the
            reservation starts."""
        ),
    )
    max_reservation_days = models.IntegerField(
        default=7,
        help_text=dedent(
            """\
            Only used when reservations are allowed. Maximum number of days for a reservation."""
        ),
    )

    def __str__(self):
        return str(self.name)

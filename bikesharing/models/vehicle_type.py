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

    def __str__(self):
        return str(self.name)

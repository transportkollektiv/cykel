from django.contrib.gis.db import models as geomodels
from django.db import models
from django.utils.translation import gettext_lazy as _


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

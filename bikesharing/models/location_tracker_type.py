from django.db import models


class LocationTrackerType(models.Model):
    name = models.CharField(default=None, null=True, blank=True, max_length=255)
    battery_voltage_warning = models.FloatField(default=None, null=True, blank=True)
    battery_voltage_critical = models.FloatField(default=None, null=True, blank=True)

    def __str__(self):
        return str(self.name)

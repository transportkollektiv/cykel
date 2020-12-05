from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _

from .location import Location


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
    tracker_type = models.ForeignKey(
        "LocationTrackerType", on_delete=models.PROTECT, null=True, blank=True
    )
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

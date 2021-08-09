from django.contrib.gis.db import models as geomodels
from django.db import models
from django.utils.translation import gettext_lazy as _


class Location(models.Model):
    class Source(models.TextChoices):
        LOCK = "LO", _("Lock")
        TRACKER = "TR", _("Tracker")
        USER = "US", _("User")
        SYSTEM = "SY", _("System")

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

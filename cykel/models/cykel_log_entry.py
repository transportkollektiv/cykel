from django.contrib.admin.options import get_content_type_for_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# log texts that only contain {object}
LOG_TEXTS_BASIC = {
    "cykel.bike.rent.unlock": _("{object} has been unlocked"),
    "cykel.bike.rent.longterm": _("{object} had a long running rent"),
    "cykel.bike.forsaken": _("{object} had no rent in some time"),
    "cykel.bike.missing_reporting": _("{object} (missing) reported its status again!"),
    "cykel.tracker.missing_reporting": _(
        "{object} (missing) reported its status again!"
    ),
}

LOG_TEXTS = {
    "cykel.bike.rent.finished.station": _(
        "{object} finished rent at Station {station} with rent {rent}"
    ),
    "cykel.bike.rent.finished.freefloat": _(
        "{object} finished rent freefloating at {location} with rent {rent}"
    ),
    "cykel.bike.rent.started.station": _(
        "{object} began rent at Station {station} with rent {rent}"
    ),
    "cykel.bike.rent.started.freefloat": _(
        "{object} began rent freefloating at {location} with rent {rent}"
    ),
    "cykel.bike.tracker.battery.critical": _(
        "{object} (on Bike {bike}) had critical battery voltage {voltage} V"
    ),
    "cykel.bike.tracker.battery.warning": _(
        "{object} (on Bike {bike}) had low battery voltage {voltage} V"
    ),
    "cykel.tracker.battery.critical": _(
        "{object} had critical battery voltage {voltage} V"
    ),
    "cykel.tracker.battery.warning": _("{object} had low battery voltage {voltage} V"),
}


class CykelLogEntry(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    action_type = models.CharField(max_length=200)
    data = models.JSONField(default=dict)

    class Meta:
        ordering = ("-timestamp",)
        verbose_name = "Log Entry"
        verbose_name_plural = "Log Entries"

    def delete(self, using=None, keep_parents=False):
        raise TypeError("Logs cannot be deleted.")

    def __str__(self):
        return (
            f"CykelLogEntry(content_object={self.content_object}, "
            + f"action_type={self.action_type}, timestamp={self.timestamp})"
        )

    @staticmethod
    def create_unless_time(timefilter, **kwargs):
        obj = kwargs["content_object"]
        action_type = kwargs["action_type"]
        if not CykelLogEntry.objects.filter(
            content_type=get_content_type_for_model(obj),
            object_id=obj.pk,
            action_type=action_type,
            timestamp__gte=timefilter,
        ).exists():
            CykelLogEntry.objects.create(**kwargs)

    def display_object(self):
        from bikesharing.models import Bike, LocationTracker

        try:
            co = self.content_object
        except ObjectDoesNotExist:
            return ""

        text = None
        data = None

        if isinstance(co, Bike):
            text = _("Bike {ref}")
            data = {
                "url": reverse(
                    "admin:%s_%s_change" % (co._meta.app_label, co._meta.model_name),
                    args=[co.id],
                ),
                "ref": co.bike_number,
            }

        if isinstance(co, LocationTracker):
            text = _("Tracker {ref}")
            data = {
                "url": reverse(
                    "admin:%s_%s_change" % (co._meta.app_label, co._meta.model_name),
                    args=[co.id],
                ),
                "ref": co.device_id,
            }

        if text and data:
            data["ref"] = format_html('<a href="{url}">{ref}</a>', **data)
            return format_html(text, **data)
        elif text:
            return text
        return ""

    def display(self):
        from bikesharing.models import Bike, Location

        if self.action_type in LOG_TEXTS_BASIC:
            return format_html(
                LOG_TEXTS_BASIC[self.action_type], object=self.display_object()
            )

        if self.action_type in LOG_TEXTS:
            fmt = LOG_TEXTS[self.action_type]
            data = {"object": self.display_object()}

            if self.action_type.startswith(
                "cykel.bike.tracker.battery."
            ) or self.action_type.startswith("cykel.tracker.battery."):
                data["voltage"] = self.data["voltage"]

            if self.action_type.startswith("cykel.bike.tracker."):
                bike_id = self.data["bike_id"]
                try:
                    bike = Bike.objects.get(pk=bike_id)
                    ref = bike.bike_number
                except ObjectDoesNotExist:
                    ref = bike_id
                bike_url = reverse("admin:bikesharing_bike_change", args=[bike_id])
                data["bike"] = format_html(
                    '<a href="{url}">{ref}</a>', url=bike_url, ref=ref
                )

            if self.action_type.startswith("cykel.bike.rent."):
                rent_id = self.data["rent_id"]
                rent_url = reverse("admin:bikesharing_rent_change", args=[rent_id])
                data["rent"] = format_html(
                    '<a href="{url}">{ref}</a>', url=rent_url, ref=rent_id
                )

            if self.action_type.startswith(
                "cykel.bike.rent."
            ) and self.action_type.endswith(".station"):
                station_id = self.data["station_id"]
                station_url = reverse(
                    "admin:bikesharing_station_change", args=[station_id]
                )
                data["station"] = format_html(
                    '<a href="{url}">{ref}</a>', url=station_url, ref=station_id
                )

            if self.action_type.startswith(
                "cykel.bike.rent."
            ) and self.action_type.endswith(".freefloat"):
                location_id = self.data["location_id"]
                if location_id:
                    try:
                        loc = Location.objects.get(pk=location_id)
                        ref = "{}, {}".format(loc.geo.y, loc.geo.x)
                    except ObjectDoesNotExist:
                        ref = location_id

                    location_url = reverse(
                        "admin:bikesharing_location_change", args=[location_id]
                    )
                    data["location"] = format_html(
                        '<a href="{url}">{ref}</a>', url=location_url, ref=ref
                    )
                else:
                    data["location"] = "[unknown]"

            return format_html(fmt, **data)

        return self.action_type

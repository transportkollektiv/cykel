from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.safestring import mark_safe
from leaflet.admin import LeafletGeoAdmin
from preferences.admin import PreferencesAdmin

from .models import (
    Bike,
    BikeSharePreferences,
    Location,
    LocationTracker,
    LocationTrackerType,
    Lock,
    LockType,
    Rent,
    Station,
    VehicleType,
)

OSM_URL = "https://www.openstreetmap.org/?mlat={lat}&mlon={lng}#map=16/{lat}/{lng}"


def format_geolocation_text(geolocation):
    lat = str(geolocation.geo.y)
    lng = str(geolocation.geo.x)
    accuracy = ""
    if geolocation.accuracy:
        accuracy = ", accuracy: " + str(geolocation.accuracy) + "m"
    timestamp = ", reported at: " + formats.localize(
        timezone.template_localtime(geolocation.reported_at)
    )
    url = OSM_URL.format(lat=lat, lng=lng)
    return "<a href='%s'>%s, %s</a>%s%s" % (
        url,
        lat,
        lng,
        accuracy,
        timestamp,
    )


def format_geolocation_text_with_source(geolocation):
    source = ""
    if geolocation.tracker:
        tracker = geolocation.tracker
        source = " (source: <a href='{url}'>tracker {device_id}</a>)".format(
            url=reverse("admin:bikesharing_locationtracker_change", args=(tracker.id,)),
            device_id=tracker.device_id,
        )
    return "%s%s" % (
        format_geolocation_text(geolocation),
        source,
    )


@admin.register(Location)
class LocationAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ("bike", "tracker", "geo", "source", "reported_at")
    list_filter = ("bike", "tracker", "source")
    search_fields = ("bike__bike_number", "tracker__device_id")
    date_hierarchy = "reported_at"


@admin.register(Lock)
class LockAdmin(admin.ModelAdmin):
    list_display = ("lock_id", "lock_type", "bike")
    list_filter = ("lock_type", "bike")
    readonly_fields = ("bike",)


@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = (
        "bike_number",
        "vehicle_type",
        "availability_status",
        "state",
        "last_reported",
        "last_rent",
    )
    list_filter = ("vehicle_type", "availability_status", "state")
    search_fields = ("bike_number", "non_static_bike_uuid")
    readonly_fields = ("location", "non_static_bike_uuid")
    ordering = ["bike_number"]

    def get_queryset(self, request):
        qs = super(BikeAdmin, self).get_queryset(request)
        qs = qs.annotate(last_rent_end=Max("rent__rent_end"))
        return qs

    @mark_safe
    def location(self, bike):
        public_info = ""
        internal_info = ""
        if bike.public_geolocation():
            public_info = "Public: %s<br>" % (
                format_geolocation_text_with_source(bike.public_geolocation())
            )
        if bike.internal_geolocation():
            internal_info = "Internal: %s" % (
                format_geolocation_text_with_source(bike.internal_geolocation())
            )
        return "%s %s" % (public_info, internal_info)

    location.allow_tags = True

    @mark_safe
    def last_rent(self, bike):
        ts = bike.last_rent_end
        if ts is None:
            return "-"
        return "<time datetime='{}' title='{}'>{}</time>".format(
            ts, ts, naturaltime(ts)
        )

    last_rent.admin_order_field = "last_rent_end"
    last_rent.allow_tags = True


@admin.register(Rent)
class RentAdmin(admin.ModelAdmin):
    list_filter = ("rent_start", "rent_end")
    search_fields = ("bike__bike_number", "user__username")
    readonly_fields = (
        "start_location_str",
        "end_location_str",
    )
    exclude = ("start_location", "end_location")
    actions = ["force_end"]

    def get_list_display(self, request):
        if request.user.has_perm("cykel.view_user"):
            return ("bike", "user", "rent_start", "rent_end")
        return ("bike", "rent_start", "rent_end")

    def get_fields(self, request, obj=None):
        default_fields = super(RentAdmin, self).get_fields(request, obj=obj)
        if not request.user.has_perm("cykel.view_user"):
            default_fields.remove("user")
        return default_fields

    @mark_safe
    def start_location_str(self, obj):
        return format_geolocation_text_with_source(obj.start_location)

    start_location_str.allow_tags = True
    start_location_str.short_description = "Start location"

    @mark_safe
    def end_location_str(self, obj):
        return format_geolocation_text_with_source(obj.end_location)

    end_location_str.allow_tags = True
    end_location_str.short_description = "End location"

    def force_end(self, request, queryset):
        for rent in queryset:
            rent.end(force=True)

    force_end.short_description = "Force end selected rents"
    force_end.allowed_permissions = ("change",)


@admin.register(LocationTracker)
class LocationTrackerAdmin(admin.ModelAdmin):
    list_display = (
        "device_id",
        "tracker_type",
        "bike",
        "last_reported",
        "battery_voltage_status",
        "tracker_status",
    )
    list_filter = (
        "tracker_type",
        "tracker_status",
    )
    search_fields = ("device_id", "bike__bike_number")
    readonly_fields = ["location"]
    ordering = ["device_id"]

    @mark_safe
    def location(self, obj):
        if obj is None or obj.current_geolocation() is None:
            return ""
        return format_geolocation_text(obj.current_geolocation())

    location.allow_tags = True

    @mark_safe
    def battery_voltage_status(self, obj):
        if obj.battery_voltage is None:
            return "-"
        if obj.tracker_type is None:
            return obj.battery_voltage
        cssclass = ""
        if (
            obj.tracker_type.battery_voltage_critical is not None
            and obj.tracker_type.battery_voltage_critical >= obj.battery_voltage
        ):
            cssclass = "critical"
        elif (
            obj.tracker_type.battery_voltage_warning is not None
            and obj.tracker_type.battery_voltage_warning >= obj.battery_voltage
        ):
            cssclass = "warning"
        if cssclass != "":
            cssclass = "battery_voltage--" + cssclass
        return "<span class='{}'>{}</span>".format(cssclass, obj.battery_voltage)

    battery_voltage_status.allow_tags = True
    battery_voltage_status.admin_order_field = "battery_voltage"
    battery_voltage_status.short_description = "Battery Voltage"

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        my_urls = [
            path(
                "by-device-id/<path:object_id>/",
                self.admin_site.admin_view(self.redir_device_id),
                name="locationtracker_device_id_redirect",
            ),
        ]
        return my_urls + urls

    def redir_device_id(self, request, object_id):
        tracker = self.get_object(request, object_id, from_field="device_id")

        if tracker is None:
            opts = self.model._meta
            return self._get_obj_does_not_exist_redirect(request, opts, object_id)

        url = reverse("admin:bikesharing_locationtracker_change", args=(tracker.id,))
        return HttpResponseRedirect(url)


@admin.register(Station)
class StationAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ("station_name", "status", "max_bikes", "bikes")
    readonly_fields = ("bikes",)

    def bikes(self, obj):
        return ", ".join([k.bike_number for k in obj.bike_set.all()])


admin.site.register(VehicleType, admin.ModelAdmin)
admin.site.register(LocationTrackerType, admin.ModelAdmin)
admin.site.register(LockType, admin.ModelAdmin)
admin.site.register(BikeSharePreferences, PreferencesAdmin)

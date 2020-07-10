from django.contrib import admin
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
    Lock,
    Rent,
    Station,
)

OSM_URL = "https://www.openstreetmap.org/?mlat={lat}&mlon={lng}#map=16/{lat}/{lng}"


@admin.register(Location)
class LocationAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ("bike", "tracker", "geo", "source", "reported_at")
    list_filter = ("bike", "tracker", "source")
    search_fields = ("bike__bike_number", "tracker__device_id")
    date_hierarchy = "reported_at"


@admin.register(Bike)
class BikeAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = (
        "bike_number",
        "bike_type",
        "availability_status",
        "state",
        "last_reported",
    )
    list_filter = ("bike_type", "availability_status", "state")
    search_fields = ("bike_number", "non_static_bike_uuid")
    readonly_fields = ("location", "non_static_bike_uuid")
    ordering = ["bike_number"]

    @mark_safe
    def location(self, bike):
        public_info = ""
        internal_info = ""
        if bike.public_geolocation():
            public_info = "Public: %s<br>" % (
                self.format_geolocation_text(bike.public_geolocation())
            )
        if bike.internal_geolocation():
            internal_info = "Internal: %s" % (
                self.format_geolocation_text(bike.internal_geolocation())
            )
        return "%s %s" % (public_info, internal_info)

    @staticmethod
    def format_geolocation_text(geolocation):
        lat = str(geolocation.geo.y)
        lng = str(geolocation.geo.x)
        accuracy = ""
        if geolocation.accuracy:
            accuracy = ", accuracy: " + str(geolocation.accuracy) + "m"
        timestamp = ", reported at: " + formats.localize(
            timezone.template_localtime(geolocation.reported_at)
        )
        source = ""
        if geolocation.tracker:
            tracker = geolocation.tracker
            source = " (source: <a href='{url}'>tracker {device_id}</a>)".format(
                url=reverse(
                    "admin:bikesharing_locationtracker_change", args=(tracker.id,)
                ),
                device_id=tracker.device_id,
            )
        url = OSM_URL.format(lat=lat, lng=lng)
        return "<a href='%s'>%s, %s</a>%s%s%s" % (
            url,
            lat,
            lng,
            accuracy,
            timestamp,
            source,
        )

    location.allow_tags = True


@admin.register(Rent)
class RentAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ("bike", "user", "rent_start", "rent_end")
    list_filter = ("rent_start", "rent_end")
    search_fields = ("bike__bike_number", "user__username")
    actions = ["force_end"]

    def force_end(self, request, queryset):
        for rent in queryset:
            rent.end()

    force_end.short_description = "Force end selected rents"
    force_end.allowed_permissions = ("change",)


@admin.register(LocationTracker)
class LocationTrackerAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = (
        "device_id",
        "tracker_type",
        "bike",
        "last_reported",
        "battery_voltage",
        "tracker_status",
    )
    list_filter = ("tracker_type", "tracker_status")
    search_fields = ("device_id", "bike__bike_number")
    readonly_fields = ["location"]
    ordering = ["device_id"]

    @mark_safe
    def location(self, obj):
        if obj is None or obj.current_geolocation() is None:
            return ""
        lat = str(obj.current_geolocation().geo.y)
        lng = str(obj.current_geolocation().geo.x)
        url = OSM_URL.format(lat=lat, lng=lng)
        return "<a href='%s'>%s, %s</a>" % (url, lat, lng)

    location.allow_tags = True


admin.site.register(Lock, LeafletGeoAdmin)
admin.site.register(Station, LeafletGeoAdmin)
admin.site.register(BikeSharePreferences, PreferencesAdmin)

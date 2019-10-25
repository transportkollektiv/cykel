from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin, LeafletGeoAdminMixin
from preferences.admin import PreferencesAdmin

from .models import Bike
from .models import Rent
from .models import Lock
from .models import Location
from .models import Station
from .models import BikeSharePreferences
from .models import LocationTracker


@admin.register(Location)
class LocationAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ('bike', 'geo', 'source', 'reported_at')
    list_filter = ('bike', 'source')
    search_fields = ('bike__bike_number', )
    date_hierarchy = 'reported_at'

@admin.register(Bike)
class BikeAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ('bike_number', 'bike_type', 'availability_status',
                    'state', 'last_reported')
    list_filter = ('bike_type', 'availability_status', 'state')
    search_fields = ('bike_number',)
    readonly_fields = ['location']

    def location(self, obj):
        if obj is None or obj.current_position() is None:
            return ""
        lat = str(obj.current_position().geo.y)
        lng = str(obj.current_position().geo.x)
        if obj.current_position().accuracy:
            accuracy = ", accuracy: " + str(obj.current_position().accuracy) + "m"
        else:
            accuracy = ""
        if (obj.current_position().tracker):
            trackerid = ", tracker: " + obj.current_position().tracker.device_id
        else:
            trackerid = ""
        return lat + ", " + lng + accuracy + trackerid + " - https://www.openstreetmap.org/?mlat="+lat+"&mlon="+lng+"#map=16/"+lat+"/"+lng+""


@admin.register(Rent)
class RentAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ('bike', 'user', 'rent_start', 'rent_end')
    list_filter = ('rent_start', 'rent_end')
    search_fields = ('bike__bike_number', 'user__username')

@admin.register(LocationTracker)
class LocationTrackerAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ('device_id',  'tracker_type', 'bike', 'last_reported', 'battery_voltage')
    list_filter = ('tracker_type', )
    search_fields = ('device_id', 'bike__bike_number')
    readonly_fields = ['location']

    def location(self, obj):
        if obj is None or obj.current_position() is None:
            return ""
        lat = str(obj.current_position().geo.y)
        lng = str(obj.current_position().geo.x)
        return lat + ", " + lng + " - https://www.openstreetmap.org/?mlat="+lat+"&mlon="+lng+"#map=16/"+lat+"/"+lng+""

admin.site.register(Lock, LeafletGeoAdmin)
admin.site.register(Station, LeafletGeoAdmin)
admin.site.register(BikeSharePreferences, PreferencesAdmin)

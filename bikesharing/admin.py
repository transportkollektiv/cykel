from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin, LeafletGeoAdminMixin
from preferences.admin import PreferencesAdmin

from .models import Bike
from .models import Rent
from .models import Lock
from .models import Location
from .models import Station
from .models import BikeSharePreferences

@admin.register(Location)
class LocationAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ('bike', 'geo', 'source', 'reported_at')
    list_filter = ('bike', 'source')
    search_fields = ('bike__bike_number', )
    date_hierarchy = 'reported_at'

class LocationInline(LeafletGeoAdminMixin, admin.StackedInline):
    model = Location
    extra = 1
    max_num = 1


@admin.register(Bike)
class BikeAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ('bike_number', 'bike_type', 'availability_status',
                    'state', 'last_reported', 'battery_voltage')
    list_filter = ('bike_type', 'availability_status', 'state')
    search_fields = ('bike_number',)
    inlines = [
        LocationInline,
    ]


@admin.register(Rent)
class RentAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    list_display = ('bike', 'user', 'rent_start', 'rent_end')
    list_filter = ('rent_start', 'rent_end')
    search_fields = ('bike__bike_number', 'user__username')


admin.site.register(Lock, LeafletGeoAdmin)
admin.site.register(Station, LeafletGeoAdmin)
admin.site.register(BikeSharePreferences, PreferencesAdmin)

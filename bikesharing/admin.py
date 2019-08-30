from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin

# Register your models here.

from .models import Bike
from .models import Rent
from .models import Lock
from .models import Station

#admin.site.register(Bike, OSMGeoAdmin)
#admin.site.register(Rent, OSMGeoAdmin)

@admin.register(Bike)
class BikeAdmin(LeafletGeoAdmin, admin.ModelAdmin):
	list_display = ('bike_number', 'bike_type', 'availability_status', 'state', 'last_reported', 'battery_voltage')
	list_filter = ('bike_type', 'availability_status', 'state')
	search_fields = ('bike_number',)

@admin.register(Rent)
class RentAdmin(LeafletGeoAdmin, admin.ModelAdmin):
	list_display = ('bike', 'user', 'rent_start', 'rent_end')
	list_filter = ('rent_start', 'rent_end')
	search_fields = ('bike__bike_number', 'user__username')

admin.site.register(Lock, LeafletGeoAdmin)
admin.site.register(Station, LeafletGeoAdmin)
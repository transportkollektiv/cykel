from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

# Register your models here.

from .models import Bike
from .models import Rent
from .models import Lock
from .models import Station

#admin.site.register(Bike, OSMGeoAdmin)
#admin.site.register(Rent, OSMGeoAdmin)

@admin.register(Bike)
class BikeAdmin(OSMGeoAdmin, admin.ModelAdmin):
	list_display = ('bike_number', 'bike_type', 'availability_status', 'state', 'last_reported', 'battery_voltage')
	list_filter = ('bike_type', 'availability_status', 'state')
	search_fields = ('bike_number',)

@admin.register(Rent)
class RentAdmin(OSMGeoAdmin, admin.ModelAdmin):
	list_display = ('bike', 'user', 'rent_start', 'rent_end')
	list_filter = ('rent_start', 'rent_end')
	search_fields = ('bike__bike_number', 'user__username', 'user__email', 'user__first_name', 'user__last_name',)

admin.site.register(Lock, OSMGeoAdmin)
admin.site.register(Station, OSMGeoAdmin)
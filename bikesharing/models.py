from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as geomodels
from macaddress.fields import MACAddressField

# Create your models here.

bike_availability_status_choices = (
	('DI', 'Disabled'),
	('IU', 'In Use'),
	('AV', 'Available')
)

bike_state_status_choices = (
	('US', 'Usable'),
	('BR', 'Broken'),
	('IR', 'In Repair'),
	('MI', 'Missing'),
)

bike_type_choices = (
	('BI', 'Bike'),
	('CB', 'Cargo Bike'),
	('EB', 'E-Bike'),
	('ES', 'E-Scooter'),
	('WH', 'Wheelchair'),
)

lock_type_choices = (
	('CL', 'Combination lock'),
	('EL', 'Electronic Lock'),
)

station_status_choices = (
	('DI', 'Disabled'),
	('AC', 'Active'),
)

class Bike(models.Model):
	bike_number = models.CharField(max_length=8)
	current_position = geomodels.PointField(default=None, null=True, blank=True)
	availability_status = models.CharField(max_length=2, choices=bike_availability_status_choices, default='DI')
	state = models.CharField(max_length=2, choices=bike_state_status_choices, default='US')
	bike_type = models.CharField(max_length=2, choices=bike_type_choices, default='BI')
	lock = models.ForeignKey('Lock', on_delete=models.PROTECT, null=True, blank=True)
	current_station = models.ForeignKey('Station', on_delete=models.PROTECT, blank=True, null=True, default=None)
	
	def __str__(self):
		return self.bike_number

class Rent(models.Model):
	rent_start = models.DateTimeField()
	rent_end = models.DateTimeField(default=None, null=True, blank=True)
	start_position = geomodels.PointField(default=None, null=True)
	start_station = models.ForeignKey('Station', default=None, on_delete=models.PROTECT, null=True, blank=True, related_name='%(class)s_start_station')
	end_position = geomodels.PointField(default=None, null=True)
	end_station = models.ForeignKey('Station', default=None, on_delete=models.PROTECT, null=True, blank=True, related_name='%(class)s_end_station')
	bike = models.ForeignKey('Bike', default=None, on_delete=models.PROTECT)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

class Lock(models.Model):
	lock_id = models.CharField(editable=True, max_length=255)
	lock_type = models.CharField(max_length=2, choices=lock_type_choices, default='CL')
	mac_address = MACAddressField(null=True, blank=True)
	unlock_key = models.CharField(editable=True, max_length=255, blank=True)

	def __str__(self):
		return str(self.lock_id)

class Station(models.Model):
	status = models.CharField(max_length=2, choices=station_status_choices, default='DI')
	station_name = models.CharField(max_length=255)
	location = geomodels.PointField(default=None, null=True)
	max_bikes = models.IntegerField(default=10)

	def __str__(self):
		return str(self.station_name)
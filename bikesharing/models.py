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
	last_reported = models.DateTimeField(default=None, null=True, blank=True)
	internal_note = models.TextField(default=None, null=True, blank=True)
	battery_voltage = models.FloatField(default=None, null=True, blank=True) #TODO Move to lock
	photo = models.FileField(upload_to='uploads/', default=None, null=True, blank=True) #TODO Thumbnail
	
	def __str__(self):
		return str(self.bike_number)

	def __repr__(self):
		return "#{bike_number} ({state}) @ {position} ({last_reported})".format(
			bike_number=self.bike_number,
			state=self.state,
			position=self.current_position,
			last_reported=self.last_reported,
			)

class Rent(models.Model):
	rent_start = models.DateTimeField()
	rent_end = models.DateTimeField(default=None, null=True, blank=True)
	start_position = geomodels.PointField(default=None, null=True)
	start_station = models.ForeignKey('Station', default=None, on_delete=models.PROTECT, null=True, blank=True, related_name='%(class)s_start_station')
	end_position = geomodels.PointField(default=None, null=True)
	end_station = models.ForeignKey('Station', default=None, on_delete=models.PROTECT, null=True, blank=True, related_name='%(class)s_end_station')
	bike = models.ForeignKey('Bike', default=None, on_delete=models.PROTECT)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

	def __repr__(self):
		return "Bike {bike} for User '{user}'\n  rented {rent_start} from {start_position}/{start_station}\n  return {rent_end} at {end_position}/{end_station}".format(
			bike=self.bike,
			user=self.user,
			start_position=self.start_position,
			start_station=self.start_station,
			rent_start=self.rent_start,
			end_position=self.end_position,
			end_station=self.end_station,
			rent_end=self.rent_end
			)

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
		return self.station_name

	def __repr__(self):
		return "Station '{station_name}', max. {max_bikes} bikes ({location})".format(
			station_name=self.station_name,
			max_bikes=self.max_bikes,
			location=self.location
			)

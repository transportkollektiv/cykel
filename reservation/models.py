from django.db import models
from bikesharing.models import Station, Bike, Rent, VehicleType
from schedule.models import Event
from django.conf import settings as django_settings

class Reservation(models.Model):
    creator = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    start_location = models.ForeignKey(Station, on_delete=models.CASCADE)
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, null=True, blank=True)
    rent = models.OneToOneField(Rent, on_delete=models.CASCADE, null=True, blank=True)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE)
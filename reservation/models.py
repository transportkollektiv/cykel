from django.conf import settings as django_settings
from django.db import models
from schedule.models import Event

from bikesharing.models import Bike, Rent, Station, VehicleType


class Reservation(models.Model):
    creator = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    start_location = models.ForeignKey(Station, on_delete=models.CASCADE)
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, null=True, blank=True)
    rent = models.OneToOneField(Rent, on_delete=models.CASCADE, null=True, blank=True)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE)

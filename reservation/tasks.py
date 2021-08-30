from celery import shared_task

from .models import Reservation
from bikesharing.models import Rent, Bike
from django.utils.timezone import now, timedelta

@shared_task
def start_rents_for_reservations():
    upcoming_reservations = Reservation.objects.filter(bike__isnull=True, event__start__lt=now()+timedelta(hours=2))
    for reservation in upcoming_reservations:
        available_bike = Bike.objects.filter(availability_status=Bike.Availability.AVAILABLE, current_station=reservation.start_location).first()
        if available_bike is not None:
            available_bike.availability_status = Bike.Availability.IN_USE
            available_bike.save()
            rent = Rent.objects.create(
                rent_start=now(),
                bike=available_bike,
                user=reservation.creator,
                start_station=available_bike.current_station,
            )
            rent.save()
            reservation.bike = available_bike
            reservation.save()

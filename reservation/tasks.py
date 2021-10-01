from celery import shared_task

from .models import Reservation
from bikesharing.models import Rent, Bike
from django.db.models import F
from django.utils.timezone import now, timedelta


@shared_task
def start_rents_for_reservations():
    upcoming_reservations = Reservation.objects.filter(rent__isnull=True, bike__isnull=True,
                                                       vehicle_type__allow_reservation__exact=True,
                                                       event__start__lt=now() + timedelta(minutes=1)
                                                                        * F(
                                                           'vehicle_type__reservation_lead_time_minutes'),
                                                       event__end__gt=now())
    for reservation in upcoming_reservations:
        available_bike = Bike.objects.filter(availability_status=Bike.Availability.AVAILABLE,
                                             state=Bike.State.USABLE,
                                             current_station=reservation.start_location,
                                             vehicle_type=reservation.vehicle_type).first()
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
            reservation.rent = rent
            reservation.save()


@shared_task
def end_reservations_of_finished_rents():
    end_reservations = Reservation.objects.filter(rent__rent_end__lt=now())
    for reservation in end_reservations:
        reservation.event.end = reservation.rent.rent_end
        reservation.event.save()

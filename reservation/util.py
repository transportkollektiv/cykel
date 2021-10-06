from django.utils.timezone import now, timedelta, make_naive
from bikesharing.models import Bike, VehicleType
from reservation.models import Reservation
from schedule.periods import Day
from datetime import time

def getRelevantReservationEvents(vehicle_type:VehicleType):
    reservations = Reservation.objects.filter(event__end__gte=now() -
                                                              timedelta(minutes=vehicle_type.reservation_lead_time_minutes),
                                              vehicle_type=vehicle_type)
    return [x.event for x in reservations]

def getNumberOfBikes(vehicle_type:VehicleType):
    bikes = Bike.objects.filter(vehicle_type=vehicle_type, state=Bike.State.USABLE)
    return len(bikes)

def getForbiddenReservationTimeRanges(day:Day, vehicle_type:VehicleType):
    maxTime = time(23, 59)
    minTime = time(0, 0)
    occurrences = day.get_occurrence_partials()
    number_of_bikes = getNumberOfBikes(vehicle_type)
    lead_time_delta = timedelta(minutes=vehicle_type.reservation_lead_time_minutes)
    forbidden_ranges = []

    for occurrence_to_check in occurrences:
        # see https://django-scheduler.readthedocs.io/en/latest/periods.html#classify-occurrence-occurrence
        if occurrence_to_check['class'] == 2:
            continue
        number_of_start_in_other_reservations = 0
        forbidden_range_end = occurrence_to_check['occurrence'].event.end
        for occurrence in occurrences:
            # ignore self
            if occurrence_to_check['occurrence'].event.id == occurrence['occurrence'].event.id:
                continue
            if occurrence_to_check['class'] == 0 or occurrence_to_check['class'] == 1:
                if occurrence['class'] == 2:
                    number_of_start_in_other_reservations += 1
                else:
                    if (occurrence_to_check['occurrence'].event.start >= occurrence['occurrence'].event.start) and (occurrence_to_check['occurrence'].event.start - lead_time_delta < occurrence['occurrence'].event.end):
                        number_of_start_in_other_reservations += 1
                        if (occurrence['class'] == 1 or occurrence['class'] == 3) and (occurrence['occurrence'].event.end < forbidden_range_end):
                            forbidden_range_end = occurrence['occurrence'].event.end
        if number_of_start_in_other_reservations + 1 >= number_of_bikes - vehicle_type.min_spontaneous_rent_vehicles:
            forbidden_range_end = make_naive(forbidden_range_end)
            forbidden_range_start = make_naive(occurrence_to_check['occurrence'].event.start)
            tomorrow = forbidden_range_end + timedelta(days=1)
            yesterday = forbidden_range_start - timedelta(days=1)

            forbidden_range_start_time = forbidden_range_start.time()
            forbidden_range_end_time = (forbidden_range_end + lead_time_delta).time()

            forbidden_range_ends_in_next_day = tomorrow.day <= (forbidden_range_end + lead_time_delta).day
            forbidden_range_starts_yesterday = yesterday.day == (forbidden_range_start - lead_time_delta).day
            if forbidden_range_starts_yesterday:
                forbidden_range_start_time = minTime
            if forbidden_range_ends_in_next_day:
                forbidden_range_end_time = maxTime
            forbidden_range = { 'start': forbidden_range_start_time, 'end': forbidden_range_end_time }
            forbidden_ranges.append(forbidden_range)

    return forbidden_ranges

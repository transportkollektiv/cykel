from django.utils.timezone import now, timedelta, make_naive
from bikesharing.models import Bike, VehicleType
from reservation.models import Reservation
from schedule.periods import Day
from datetime import time, datetime

def get_relevant_reservation_events(vehicle_type:VehicleType):
    reservations = Reservation.objects.filter(event__end__gte=now() -
                                                              timedelta(minutes=vehicle_type.reservation_lead_time_minutes),
                                              vehicle_type=vehicle_type)
    return [x.event for x in reservations]

def get_number_of_bikes(vehicle_type:VehicleType):
    bikes = Bike.objects.filter(vehicle_type=vehicle_type, state=Bike.State.USABLE)
    return len(bikes)

def get_forbidden_reservation_time_ranges(day:Day, vehicle_type:VehicleType):
    maxTime = time(23, 59)
    minTime = time(0, 0)
    occurrences = day.get_occurrence_partials()
    number_of_bikes = get_number_of_bikes(vehicle_type)
    lead_time_delta = timedelta(minutes=vehicle_type.reservation_lead_time_minutes)
    forbidden_ranges = []
    all_occurrences_go_entire_day = True

    for occurrence_to_check in occurrences:
        # see https://django-scheduler.readthedocs.io/en/latest/periods.html#classify-occurrence-occurrence
        if occurrence_to_check['class'] == 2:
            continue
        all_occurrences_go_entire_day = False

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
            # Determine end of forbidden range
            forbidden_range_end = make_naive(forbidden_range_end)
            tomorrow = make_naive(day.end) - timedelta(hours=1)
            forbidden_range_ends_in_next_day = tomorrow <= (forbidden_range_end + lead_time_delta)
            forbidden_range_end_time = (forbidden_range_end + lead_time_delta).time()
            if forbidden_range_ends_in_next_day:
                forbidden_range_end_time = maxTime
            # Determine start of forbidden range
            forbidden_range_start = make_naive(occurrence_to_check['occurrence'].event.start)
            yesterday = make_naive(day.start) - timedelta(days=1)
            forbidden_range_starts_yesterday = yesterday.date() >= (forbidden_range_start - lead_time_delta).date()
            forbidden_range_start_time = (forbidden_range_start - lead_time_delta).time()

            if forbidden_range_starts_yesterday or occurrence_to_check['class'] == 3:
                forbidden_range_start_time = minTime

            forbidden_range = { 'start': forbidden_range_start_time, 'end': forbidden_range_end_time }
            forbidden_ranges.append(forbidden_range)

    if all_occurrences_go_entire_day and len(occurrences) >= number_of_bikes - vehicle_type.min_spontaneous_rent_vehicles:
        forbidden_range = { 'start': minTime, 'end': maxTime }
        forbidden_ranges.append(forbidden_range)

    return forbidden_ranges

def is_allowed_reservation_day(day:Day, vehicle_type:VehicleType):
    occurrences = day.get_occurrence_partials()
    number_of_occ = len(occurrences)
    for occurrence in occurrences:
        # see https://django-scheduler.readthedocs.io/en/latest/periods.html#classify-occurrence-occurrence
        start_time = make_naive(occurrence['occurrence'].start)
        start_time_with_delta = (start_time - timedelta(minutes=vehicle_type.reservation_lead_time_minutes)).date()
        end_time = make_naive(occurrence['occurrence'].end)
        end_time_with_delta = (end_time + timedelta(minutes=vehicle_type.reservation_lead_time_minutes)).date()
        if day.start.date() < start_time.date():
            number_of_occ -= 1
        elif occurrence['class'] == 0:
            if not (start_time.date() > start_time_with_delta):
                number_of_occ -= 1
        elif occurrence['class'] == 1:
            if not ((start_time.date() > start_time_with_delta) and (end_time.date() < end_time_with_delta)):
                number_of_occ -= 1
        elif occurrence['class'] == 3:
            if not (end_time.date() < end_time_with_delta):
                number_of_occ -= 1

    number_of_bikes = get_number_of_bikes(vehicle_type)
    if number_of_bikes - number_of_occ - vehicle_type.min_spontaneous_rent_vehicles > 0:
        return True
    else:
        return False

def get_maximum_reservation_date(start_date_time:datetime, vehicle_type:VehicleType):
    start_time = time(23, 59)
    max_reservation_date = start_date_time
    events = get_relevant_reservation_events(vehicle_type)
    max_reservation_days = vehicle_type.max_reservation_days

    for day_delta in range(max_reservation_days + 1):
        day_to_check = start_date_time + timedelta(days=day_delta) # 0 - max reservation time
        day_period = Day(events, day_to_check)
        forbidden_ranges = get_forbidden_reservation_time_ranges(day_period, vehicle_type)
        forbidden_ranges_relevant = False
        if forbidden_ranges:
            for forbidden_range in forbidden_ranges:
                # ignore forbidden range if it ends before reservation starts, can only happen on first day
                if day_delta == 0:
                    if day_to_check.time() > forbidden_range['end']:
                        continue
                forbidden_ranges_relevant = True
                if start_time > forbidden_range['start']:
                    start_time = forbidden_range['start']
            if forbidden_ranges_relevant:
                max_reservation_date = (day_to_check.replace(hour = start_time.hour, minute = start_time.minute))
                break
        if day_delta == max_reservation_days:
            max_reservation_date = day_to_check.replace(hour = start_time.hour, minute = start_time.minute)

    return max_reservation_date

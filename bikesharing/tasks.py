from celery import shared_task
from django.db.models import Exists, OuterRef
from django.utils.timezone import now, timedelta

from cykel.models import CykelLogEntry

from .models import Bike, LocationTracker, Rent


@shared_task
def log_long_running_rents():
    rent_longtime_slope = now() - timedelta(hours=4)
    rents = Rent.objects.filter(
        rent_end__isnull=True, rent_start__lte=rent_longtime_slope
    )
    for rent in rents:
        donotremindin = now() - timedelta(hours=48)
        CykelLogEntry.create_unless_time(
            donotremindin, content_object=rent, action_type="cykel.bike.rent.longterm"
        )


@shared_task
def log_unused_bikes():
    bikes_without_rents = Bike.objects.filter(
        ~Exists(Rent.objects.filter(bike=OuterRef("pk"))),
        availability_status=Bike.Availability.AVAILABLE,
    )

    threedays = now() - timedelta(days=3)
    bikes_forsaken = Bike.objects.filter(
        ~Exists(Rent.objects.filter(bike=OuterRef("pk"), rent_end__gte=threedays)),
        availability_status=Bike.Availability.AVAILABLE,
    )

    bikes = bikes_without_rents | bikes_forsaken
    for bike in bikes:
        donotremindin = now() - timedelta(days=3)
        CykelLogEntry.create_unless_time(
            donotremindin, content_object=bike, action_type="cykel.bike.forsaken"
        )


@shared_task
def log_missing_tracker_updates():
    twohours = now() - timedelta(hours=2)
    trackers_missing = LocationTracker.objects.filter(
        tracker_status=LocationTracker.Status.ACTIVE, last_reported__lte=twohours
    )

    for tracker in trackers_missing:
        action_type = "cykel.tracker.missed_checkin"
        data = {}
        if tracker.bike:
            action_type = "cykel.bike.tracker.missed_checkin"
            data["bike_id"] = tracker.bike.pk
        eighthours = now() - timedelta(hours=8)
        CykelLogEntry.create_unless_time(
            eighthours,
            content_object=tracker,
            action_type=action_type,
            data=data
        )

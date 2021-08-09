import uuid

import requests
from django.conf import settings
from django.contrib.gis.measure import D
from django.db import models
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.utils.timezone import now
from preferences import preferences

from cykel.models import CykelLogEntry

from .bike import Bike
from .lock_type import LockType
from .station import Station


class Rent(models.Model):
    rent_start = models.DateTimeField()
    rent_end = models.DateTimeField(default=None, null=True, blank=True)
    start_location = models.ForeignKey(
        "Location",
        default=None,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)s_start_location",
    )
    start_station = models.ForeignKey(
        "Station",
        default=None,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)s_start_station",
    )
    end_location = models.ForeignKey(
        "Location",
        default=None,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)s_end_location",
    )
    end_station = models.ForeignKey(
        "Station",
        default=None,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)s_end_station",
    )
    bike = models.ForeignKey("Bike", default=None, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __repr__(self):
        return """Rent #{id}: Bike {bike} for User '{user}'\n  rented {rent_start}
            from {start_location}/{start_station}\n  return {rent_end}
            at {end_location}/{end_station}""".format(
            id=self.id,
            bike=self.bike,
            user=self.user,
            start_location=self.start_location,
            start_station=self.start_station,
            rent_start=self.rent_start,
            end_location=self.end_location,
            end_station=self.end_station,
            rent_end=self.rent_end,
        )

    def unlock(self):
        if self.bike.lock is None:
            return {}

        lock = self.bike.lock
        lock_type = lock.lock_type

        if lock_type is None:
            return {}

        if lock_type.form_factor == LockType.FormFactor.COMBINATION_LOCK:
            return {"unlock_key": self.bike.lock.unlock_key}

        if lock_type.form_factor == LockType.FormFactor.ELECTRONIC_LOCK:
            url = "{url}/{device_id}/unlock".format(
                url=lock_type.endpoint_url, device_id=lock.lock_id
            )
            r = requests.post(url)
            data = r.json()
            return {"data": data}

        return {}

    def end(self, end_location=None, force=False):
        self.rent_end = now()
        if end_location:
            self.end_location = end_location
        elif self.bike.public_geolocation():
            self.end_location = self.bike.public_geolocation()

        self.save()

        if self.end_location:
            # attach bike to station if location is closer than X meters
            # distance is configured in preferences
            max_distance = preferences.BikeSharePreferences.station_match_max_distance
            station_closer_than_Xm = Station.objects.filter(
                location__distance_lte=(self.end_location.geo, D(m=max_distance)),
                status=Station.Status.ACTIVE,
            ).first()
            if station_closer_than_Xm:
                self.bike.current_station = station_closer_than_Xm
                self.end_station = station_closer_than_Xm
                self.save()
            else:
                self.bike.current_station = None

        # set Bike status back to available
        self.bike.availability_status = Bike.Availability.AVAILABLE
        self.bike.save()
        try:
            # set new non static bike ID, so for GBFS observers can not track this bike
            self.bike.non_static_bike_uuid = uuid.uuid4()
            self.bike.save()
        except IntegrityError:
            # Congratulations! The 2^64 chance of uuid4 collision has happend.
            # here coul'd be the place for the famous comment: "should never happen"
            # So we catch this error here, but don't handle it.
            # because don't rotating a uuid every 18,446,744,073,709,551,615 rents is ok
            pass

        if self.end_station:
            CykelLogEntry.objects.create(
                content_object=self.bike,
                action_type="cykel.bike.rent.finished.station",
                data={
                    "rent_id": self.id,
                    "trip_duration": int(
                        (self.rent_end - self.rent_start).total_seconds()
                    ),
                    "station_id": self.end_station.id,
                    **({"forced": True} if force else {}),
                },
            )
        else:
            CykelLogEntry.objects.create(
                content_object=self.bike,
                action_type="cykel.bike.rent.finished.freefloat",
                data={
                    "rent_id": self.id,
                    "trip_duration": int(
                        (self.rent_end - self.rent_start).total_seconds()
                    ),
                    "location_id": getattr(self.end_location, "id", None),
                    **({"forced": True} if force else {}),
                },
            )


@receiver(models.signals.post_save, sender=Rent)
def rent_started(sender, instance, created, *args, **kwargs):
    # only interested in the first save
    if not created:
        return
    if instance.start_station:
        CykelLogEntry.objects.create(
            content_object=instance.bike,
            action_type="cykel.bike.rent.started.station",
            data={
                "rent_id": instance.id,
                "station_id": instance.start_station.id,
            },
        )
    else:
        CykelLogEntry.objects.create(
            content_object=instance.bike,
            action_type="cykel.bike.rent.started.freefloat",
            data={
                "rent_id": instance.id,
                "location_id": getattr(instance.start_location, "id", None),
            },
        )

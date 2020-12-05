from django.db import models
from preferences.models import Preferences


class BikeSharePreferences(Preferences):
    station_match_max_distance = models.IntegerField(default=20)
    gbfs_hide_bikes_after_location_report_silence = models.BooleanField(
        default=False,
        help_text="""If activated, vehicles will disappear from GBFS,
         if there was no location report in the configured time period.""",
    )
    gbfs_hide_bikes_after_location_report_hours = models.IntegerField(
        default=1,
        help_text="""Time period (in hours) after the vehicles will
         be hidden from GBFS, if there was no location report.
         Needs 'Gbfs hide bikes after location report silence' activated.""",
    )
    gbfs_system_id = models.CharField(editable=True, max_length=255, default="")
    system_name = models.CharField(editable=True, max_length=255, default="")
    system_short_name = models.CharField(editable=True, max_length=255, default="")

from django.db import migrations, models

# would be using Location.Source.SYSTEM, but apps.get_model doesn't allow access
LOCATION_SOURCE_SYSTEM = "SY"


def create_locations_for_rent_start_positions(apps, schema_editor):
    Location = apps.get_model("bikesharing", "Location")
    Rent = apps.get_model("bikesharing", "Rent")

    for rent in Rent.objects.filter(
        start_position__isnull=False, start_location__isnull=True
    ):
        loc = Location.objects.create(
            bike=rent.bike,
            geo=rent.start_position,
            source=LOCATION_SOURCE_SYSTEM,
            reported_at=rent.rent_start,
        )
        loc.save()
        rent.start_location = loc
        rent.start_position = None
        rent.save()


def create_locations_for_rent_end_positions(apps, schema_editor):
    Location = apps.get_model("bikesharing", "Location")
    Rent = apps.get_model("bikesharing", "Rent")

    for rent in Rent.objects.filter(
        end_position__isnull=False, end_location__isnull=True
    ):
        loc = Location.objects.create(
            bike=rent.bike,
            geo=rent.end_position,
            source=LOCATION_SOURCE_SYSTEM,
            reported_at=rent.rent_end,
        )
        loc.save()
        rent.end_location = loc
        rent.end_position = None
        rent.save()


class Migration(migrations.Migration):

    dependencies = [
        ("bikesharing", "0044_rent_locations_20201204_1919"),
    ]

    operations = [
        migrations.AlterField(
            model_name="location",
            name="source",
            field=models.CharField(
                choices=[
                    ("LO", "Lock"),
                    ("TR", "Tracker"),
                    ("US", "User"),
                    ("SY", "System"),
                ],
                default="LO",
                max_length=2,
            ),
        ),
        migrations.RunPython(create_locations_for_rent_start_positions),
        migrations.RunPython(create_locations_for_rent_end_positions),
    ]

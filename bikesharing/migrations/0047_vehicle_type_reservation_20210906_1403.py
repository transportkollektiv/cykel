from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bikesharing", "0046_rent_remove_position_20201204_2059"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicletype",
            name="allow_spontaneous_rent",
            field=models.BooleanField(
                default=True,
            ),
        ),
        migrations.AddField(
            model_name="vehicletype",
            name="allow_reservation",
            field=models.BooleanField(
                default=False,
            ),
        ),
        migrations.AddField(
            model_name="vehicletype",
            name="min_spontaneous_rent_vehicles",
            field=models.IntegerField(
                default=0,
            ),
        ),
        migrations.AddField(
            model_name="vehicletype",
            name="min_reservation_vehicles",
            field=models.IntegerField(
                default=0,
            ),
        ),
        migrations.AddField(
            model_name="vehicletype",
            name="reservation_lead_time_minutes",
            field=models.IntegerField(
                default=120,
            ),
        ),
        migrations.AddField(
            model_name="vehicletype",
            name="max_reservation_days",
            field=models.IntegerField(
                default=7,
            ),
        ),
    ]

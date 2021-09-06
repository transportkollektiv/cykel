from textwrap import dedent

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('bikesharing', '0047_auto_20210824_1559'),
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
    ]

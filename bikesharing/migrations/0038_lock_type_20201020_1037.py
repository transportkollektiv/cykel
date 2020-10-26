from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("bikesharing", "0037_auto_20201012_1352"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lock",
            name="mac_address",
        ),
        migrations.CreateModel(
            name="LockType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, default=None, max_length=255, null=True
                    ),
                ),
                (
                    "form_factor",
                    models.CharField(
                        choices=[("CL", "Combination lock"), ("EL", "Electronic Lock")],
                        default="CL",
                        max_length=2,
                    ),
                ),
                ("endpoint_url", models.URLField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.RenameField("Lock", "lock_type", "form_factor"),
        migrations.AddField(
            model_name="lock",
            name="lock_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="bikesharing.LockType",
            ),
        ),
    ]

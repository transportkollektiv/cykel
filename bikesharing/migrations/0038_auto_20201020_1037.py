from django.db import migrations, models
import django.db.models.deletion


def create_and_assign_lock_types(apps, schema_editor):
    Lock = apps.get_model("bikesharing", "Lock")
    LockType = apps.get_model("bikesharing", "LockType")
    used_lock_types = []
    for lock in Lock.objects.order_by("form_factor").distinct("form_factor"):
        used_lock_types.append(lock.lock_type)
    if len(used_lock_types) == 0:
        used_lock_types = ["CL"]
    if "CL" in used_lock_types:
        lt = LockType.objects.create(name="Combination Lock", form_factor="CL")
        lt.save()
        Lock.objects.filter(form_factor="CL").update(form_factor=None, lock_type=lt)
    if "EL" in used_lock_types:
        lt = LockType.objects.create(name="Electronic Lock", form_factor="EL")
        lt.save()
        Lock.objects.filter(form_factor="EL").update(form_factor=None, lock_type=lt)


def remove_lock_types(apps, schema_editor):
    Lock = apps.get_model("bikesharing", "Lock")
    LockType = apps.get_model("bikesharing", "LockType")
    for lt in LockType.objects.all():
        Lock.objects.filter(lock_type=lt).update(
            form_factor=lt.form_factor, lock_type=None
        )
        lt.delete()


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
        migrations.RunPython(create_and_assign_lock_types, remove_lock_types),
    ]

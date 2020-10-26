from django.db import migrations


def create_and_assign_lock_types(apps, schema_editor):
    Lock = apps.get_model("bikesharing", "Lock")
    LockType = apps.get_model("bikesharing", "LockType")
    used_form_factors = []
    for lock in Lock.objects.order_by("form_factor").distinct("form_factor"):
        used_form_factors.append(lock.form_factor)
    if len(used_form_factors) == 0:
        used_form_factors = ["CL"]
    if "CL" in used_form_factors:
        lt = LockType.objects.create(name="Combination Lock", form_factor="CL")
        lt.save()
        Lock.objects.filter(form_factor="CL").update(lock_type=lt)
    if "EL" in used_form_factors:
        lt = LockType.objects.create(name="Electronic Lock", form_factor="EL")
        lt.save()
        Lock.objects.filter(form_factor="EL").update(lock_type=lt)


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
        ("bikesharing", "0038_lock_type_20201020_1037"),
    ]

    operations = [
        migrations.RunPython(create_and_assign_lock_types, remove_lock_types),
    ]

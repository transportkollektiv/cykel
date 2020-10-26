from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bikesharing", "0039_move_lock_types_20201020_1040"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lock",
            name="form_factor",
        ),
    ]

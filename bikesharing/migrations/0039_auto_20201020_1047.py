from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bikesharing", "0038_auto_20201020_1037"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lock",
            name="form_factor",
        ),
    ]

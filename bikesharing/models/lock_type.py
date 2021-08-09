from django.db import models
from django.utils.translation import gettext_lazy as _


class LockType(models.Model):
    class FormFactor(models.TextChoices):
        COMBINATION_LOCK = "CL", _("Combination lock")
        ELECTRONIC_LOCK = "EL", _("Electronic Lock")

    name = models.CharField(default=None, null=True, blank=True, max_length=255)
    form_factor = models.CharField(
        max_length=2, choices=FormFactor.choices, default=FormFactor.COMBINATION_LOCK
    )
    endpoint_url = models.URLField(default=None, null=True, blank=True)

    def __str__(self):
        return str(self.name)

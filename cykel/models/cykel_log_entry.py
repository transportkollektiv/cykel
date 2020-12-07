from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class CykelLogEntry(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    action_type = models.CharField(max_length=200)
    data = models.JSONField(default=dict)

    class Meta:
        ordering = ("-timestamp",)
        verbose_name = "Log Entry"
        verbose_name_plural = "Log Entries"

    def delete(self, using=None, keep_parents=False):
        raise TypeError("Logs cannot be deleted.")

    def __str__(self):
        return (
            f"CykelLogEntry(content_object={self.content_object}, "
            + f"action_type={self.action_type}, timestamp={self.timestamp})"
        )

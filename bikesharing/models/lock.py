from django.db import models


class Lock(models.Model):
    lock_id = models.CharField(editable=True, max_length=255)
    lock_type = models.ForeignKey(
        "LockType", on_delete=models.PROTECT, null=True, blank=True
    )
    unlock_key = models.CharField(editable=True, max_length=255, blank=True)

    def __str__(self):
        return "#{lock_id} ({lock_type})".format(
            lock_id=self.lock_id, lock_type=self.lock_type
        )

    def __repr__(self):
        return """#{lock_id} ({lock_type}) unlock_key={unlock_key}""".format(
            lock_id=self.lock_id,
            lock_type=self.lock_type,
            unlock_key=self.unlock_key,
        )

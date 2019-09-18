from django.apps import AppConfig


class GbfsConfig(AppConfig):
    name = 'gbfs'
    def ready(self):
        from gbfs import handlers

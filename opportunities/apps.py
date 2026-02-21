import os
import sys

from django.conf import settings
from django.apps import AppConfig


class OpportunitiesConfig(AppConfig):
    name = 'opportunities'

    def ready(self):
        if any(
            cmd in sys.argv
            for cmd in ["migrate", "makemigrations", "collectstatic", "test", "shell", "check", "createsuperuser"]
        ):
            return

        # Avoid duplicate scheduler startup in development autoreload.
        if settings.DEBUG and os.environ.get("RUN_MAIN") != "true":
            return

        from .scheduler import start_scheduler

        start_scheduler()

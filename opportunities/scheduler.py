import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

from .services import run_iit_scraper

logger = logging.getLogger(__name__)
_scheduler = None


def _run_scraper_job():
    created = run_iit_scraper()
    logger.info("Auto scraper run completed. New items added: %s", created)


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    _scheduler.add_job(
        _run_scraper_job,
        "interval",
        minutes=10,
        id="opportunities_auto_scraper",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("APScheduler started: opportunities scraper scheduled every 10 minutes.")
    atexit.register(_shutdown_scheduler)


def _shutdown_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down.")

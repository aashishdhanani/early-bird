"""Job scheduler for daily news digest."""
import signal
import sys
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from src.config.settings import settings
from src.utils.logger import logger


class JobScheduler:
    """Manages scheduled execution of the news pipeline."""

    def __init__(self, pipeline_func):
        """
        Initialize the scheduler.

        Args:
            pipeline_func: Function to execute on schedule
        """
        self.pipeline_func = pipeline_func
        self.scheduler = BlockingScheduler()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up graceful shutdown on SIGINT and SIGTERM."""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal, stopping scheduler...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def schedule_daily(self):
        """Schedule the pipeline to run daily at configured time."""
        # Parse time from config (format: "HH:MM")
        time_parts = settings.schedule_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])

        # Get timezone
        timezone = pytz.timezone(settings.schedule_timezone)

        # Create cron trigger
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=timezone
        )

        # Add job
        self.scheduler.add_job(
            func=self.pipeline_func,
            trigger=trigger,
            id='daily_digest',
            name='Daily News Digest',
            replace_existing=True
        )

        logger.info(f"Scheduled daily digest for {settings.schedule_time} {settings.schedule_timezone}")
        logger.info(f"Next run: {self.scheduler.get_jobs()[0].next_run_time}")

    def start(self):
        """Start the scheduler (blocking)."""
        if not settings.schedule_enabled:
            logger.warning("Scheduling is disabled in config.yaml")
            return

        try:
            logger.info("Starting scheduler...")
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def run_immediately(self):
        """Run the pipeline immediately (for testing)."""
        logger.info("Running pipeline immediately...")
        try:
            self.pipeline_func()
        except Exception as e:
            logger.error(f"Error running pipeline: {e}")
            raise

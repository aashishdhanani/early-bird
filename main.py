#!/usr/bin/env python3
"""
Early Bird - Daily AI & Robotics News Aggregator

Collects, filters, and delivers a daily digest of AI and robotics news
from premium RSS sources.
"""
import argparse
import sys
import os
from datetime import datetime

from src.collectors.rss_collector import RSSCollector
from src.processors.deduplicator import Deduplicator
from src.processors.filter import ArticleFilter
from src.processors.ai_summarizer import AISummarizer
from src.composers.html_builder import HTMLBuilder
from src.senders.email_sender import EmailSender
from src.senders.gmail_api_sender import GmailAPISender
from src.scheduler.job_scheduler import JobScheduler
from src.config.settings import settings
from src.utils.logger import logger


def get_email_sender():
    """Get the appropriate email sender based on EMAIL_METHOD setting."""
    email_method = os.getenv('EMAIL_METHOD', 'smtp').lower()

    if email_method == 'gmail_api':
        logger.info("Using Gmail API for email delivery")
        return GmailAPISender()
    else:
        logger.info("Using SMTP for email delivery")
        return EmailSender()


def run_pipeline():
    """
    Execute the complete news aggregation pipeline.

    Steps:
    1. Collect articles from all RSS sources
    2. Deduplicate articles
    3. Filter and rank by relevance
    4. Generate AI summaries (optional)
    5. Compose HTML email
    6. Send email to recipient
    """
    start_time = datetime.now()
    logger.info("=" * 70)
    logger.info("Starting Early Bird pipeline")
    logger.info("=" * 70)

    try:
        # Step 1: Collect articles from RSS feeds
        logger.info("Step 1/6: Collecting articles from RSS feeds...")
        collector = RSSCollector()
        articles = collector.collect_all()

        if not articles:
            logger.warning("No articles collected, skipping rest of pipeline")
            return

        # Step 2: Deduplicate articles
        logger.info("Step 2/6: Deduplicating articles...")
        deduplicator = Deduplicator()
        unique_articles = deduplicator.deduplicate(articles)

        if not unique_articles:
            logger.warning("No unique articles after deduplication")
            return

        # Step 3: Filter and rank by relevance
        logger.info("Step 3/6: Filtering and ranking articles...")
        article_filter = ArticleFilter()
        filtered_articles = article_filter.filter_and_rank(unique_articles)

        if not filtered_articles:
            logger.warning("No articles passed relevance filter")
            return

        # Step 4: Generate AI summaries (optional)
        logger.info("Step 4/6: Generating AI summaries...")
        ai_summarizer = AISummarizer()
        filtered_articles = ai_summarizer.batch_summarize(filtered_articles)

        # Step 5: Compose email
        logger.info("Step 5/6: Composing email...")
        html_builder = HTMLBuilder()
        html_content = html_builder.build_html(filtered_articles)
        plain_text_content = html_builder.build_plain_text(filtered_articles)

        # Save preview HTML for debugging
        html_builder.preview_html(html_content)

        # Step 6: Send email
        logger.info("Step 6/6: Sending email...")
        email_sender = get_email_sender()

        # Gmail API sender has different signature
        if isinstance(email_sender, GmailAPISender):
            success = email_sender.send_digest(
                recipient=settings.email_recipient,
                html_content=html_content,
                plain_text_content=plain_text_content,
                article_count=len(filtered_articles),
                subject_prefix=settings.email_subject_prefix
            )
        else:
            success = email_sender.send_digest(
                html_content=html_content,
                plain_text_content=plain_text_content,
                article_count=len(filtered_articles)
            )

        if success:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info("=" * 70)
            logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds")
            logger.info(f"Sent digest with {len(filtered_articles)} articles")
            logger.info("=" * 70)
        else:
            logger.error("Failed to send email")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise


def run_now():
    """Run the pipeline immediately (for testing)."""
    logger.info("Running pipeline immediately...")
    run_pipeline()


def run_scheduler():
    """Run the scheduler (production mode)."""
    logger.info("Starting Early Bird in scheduled mode...")
    logger.info(f"Will run daily at {settings.schedule_time} {settings.schedule_timezone}")

    scheduler = JobScheduler(pipeline_func=run_pipeline)
    scheduler.schedule_daily()
    scheduler.start()


def send_test_email():
    """Send a test email to verify configuration."""
    logger.info("Sending test email...")

    try:
        email_sender = get_email_sender()

        # Gmail API sender has different signature
        if isinstance(email_sender, GmailAPISender):
            success = email_sender.send_test_email(recipient=settings.email_recipient)
        else:
            success = email_sender.send_test_email()

        if success:
            logger.info("Test email sent successfully!")
            logger.info("Check your inbox to verify receipt.")
        else:
            logger.error("Failed to send test email")
            logger.error("Check your email configuration in .env file")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error sending test email: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Early Bird - Daily AI & Robotics News Aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run pipeline immediately (for testing)
  python main.py --run-now

  # Start scheduler (production mode)
  python main.py --schedule

  # Send test email
  python main.py --test-email

Configuration:
  Edit config.yaml for RSS sources and settings
  Edit .env for email credentials
        """
    )

    parser.add_argument(
        '--run-now',
        action='store_true',
        help='Run the pipeline immediately (for testing)'
    )

    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run in scheduled mode (production)'
    )

    parser.add_argument(
        '--test-email',
        action='store_true',
        help='Send a test email to verify configuration'
    )

    args = parser.parse_args()

    # Show banner
    print("=" * 70)
    print("🐦 EARLY BIRD - AI & Robotics News Aggregator")
    print("=" * 70)
    print()

    # Execute based on arguments
    if args.test_email:
        send_test_email()
    elif args.run_now:
        run_now()
    elif args.schedule:
        run_scheduler()
    else:
        parser.print_help()
        print()
        print("Please specify an operation: --run-now, --schedule, or --test-email")
        sys.exit(1)


if __name__ == "__main__":
    main()

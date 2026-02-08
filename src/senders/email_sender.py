"""Email sender using SMTP (supports Gmail and SendGrid)."""
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional

from src.config.settings import settings
from src.utils.logger import logger


class EmailSender:
    """Sends emails via SMTP (supports Gmail and SendGrid)."""

    def __init__(self):
        """Initialize email sender."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.use_tls = settings.smtp_use_tls
        self.sender_email = settings.email_sender
        self.sender_password = settings.email_password
        self.is_sendgrid = settings.is_sendgrid
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def send_email(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        plain_text_content: str
    ) -> bool:
        """
        Send email with HTML and plain text versions.

        Args:
            recipient: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_text_content: Plain text email body

        Returns:
            True if email sent successfully, False otherwise
        """
        logger.info(f"Preparing to send email to {recipient}...")

        # Create message
        message = MIMEMultipart('alternative')
        message['From'] = self.sender_email
        message['To'] = recipient
        message['Subject'] = subject
        message['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

        # Attach plain text version (fallback)
        part1 = MIMEText(plain_text_content, 'plain', 'utf-8')
        message.attach(part1)

        # Attach HTML version
        part2 = MIMEText(html_content, 'html', 'utf-8')
        message.attach(part2)

        # Send with retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Sending email (attempt {attempt}/{self.max_retries})...")

                # Connect to SMTP server
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    # Enable TLS
                    if self.use_tls:
                        server.starttls()

                    # Login (SendGrid uses "apikey" as username, Gmail uses email)
                    username = "apikey" if self.is_sendgrid else self.sender_email
                    server.login(username, self.sender_password)

                    # Send email
                    server.send_message(message)

                logger.info(f"Email sent successfully to {recipient}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication failed: {e}")
                logger.error("Check your email credentials in .env file")
                if self.is_sendgrid:
                    logger.error("Make sure you're using a valid SendGrid API key (starts with SG.)")
                else:
                    logger.error("Make sure you're using an app-specific password if using Gmail")
                return False

            except smtplib.SMTPException as e:
                logger.error(f"SMTP error on attempt {attempt}: {e}")
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached, email not sent")
                    return False

            except Exception as e:
                logger.error(f"Unexpected error sending email: {e}")
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached, email not sent")
                    return False

        return False

    def send_digest(
        self,
        html_content: str,
        plain_text_content: str,
        article_count: int,
        date: Optional[str] = None
    ) -> bool:
        """
        Send daily digest email.

        Args:
            html_content: HTML email body
            plain_text_content: Plain text email body
            article_count: Number of articles in digest
            date: Date string (defaults to today)

        Returns:
            True if email sent successfully
        """
        if date is None:
            date = datetime.now().strftime("%B %d, %Y")

        # Build subject line
        subject = f"{settings.email_subject_prefix}: {date} - {article_count} AI & Robotics Updates"

        # Get recipient from settings
        recipient = settings.email_recipient

        # Send email
        return self.send_email(
            recipient=recipient,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text_content
        )

    def send_test_email(self) -> bool:
        """
        Send a test email to verify configuration.

        Returns:
            True if test email sent successfully
        """
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #667eea;">🐦 Early Bird Test Email</h1>
            <p>This is a test email from your Early Bird news aggregator.</p>
            <p>If you received this, your email configuration is working correctly!</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Sent from Early Bird at {datetime}
            </p>
        </body>
        </html>
        """.format(datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        plain_text = """
EARLY BIRD TEST EMAIL

This is a test email from your Early Bird news aggregator.

If you received this, your email configuration is working correctly!

---
Sent from Early Bird at {datetime}
        """.format(datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        subject = "Early Bird - Test Email"
        recipient = settings.email_recipient

        logger.info("Sending test email...")
        return self.send_email(
            recipient=recipient,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text
        )

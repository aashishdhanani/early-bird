"""Email sender using Gmail API (no app password required)."""
import os
import base64
import pickle
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.logger import logger


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailAPISender:
    """Sends emails using Gmail API with OAuth2."""

    def __init__(self):
        """Initialize Gmail API sender."""
        self.project_root = Path(__file__).parent.parent.parent
        self.credentials_file = self.project_root / "credentials.json"
        self.token_file = self.project_root / "token.pickle"
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None

        # Load saved credentials if they exist
        if self.token_file.exists():
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded saved Gmail API credentials")
            except Exception as e:
                logger.warning(f"Error loading saved credentials: {e}")

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired Gmail API credentials...")
                try:
                    creds.refresh(Request())
                    logger.info("Credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None

            # Need to do full OAuth flow
            if not creds:
                if not self.credentials_file.exists():
                    raise FileNotFoundError(
                        f"Gmail API credentials file not found: {self.credentials_file}\n"
                        f"Please follow the setup instructions:\n"
                        f"1. Go to https://console.cloud.google.com/\n"
                        f"2. Enable Gmail API\n"
                        f"3. Create OAuth credentials\n"
                        f"4. Download as 'credentials.json' and place in project root"
                    )

                logger.info("Starting OAuth2 authentication flow...")
                logger.info("A browser window will open for you to authorize the app")

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("OAuth2 authentication successful!")

            # Save credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("Saved Gmail API credentials")

        # Build service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API service initialized")
        except Exception as e:
            logger.error(f"Error building Gmail API service: {e}")
            raise

    def send_email(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        plain_text_content: str,
        sender: str = "me"
    ) -> bool:
        """
        Send email using Gmail API.

        Args:
            recipient: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_text_content: Plain text email body
            sender: Sender (use "me" for authenticated user)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            logger.info(f"Preparing to send email to {recipient} via Gmail API...")

            # Create message
            message = MIMEMultipart('alternative')
            message['To'] = recipient
            message['Subject'] = subject
            message['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

            # Attach plain text and HTML versions
            part1 = MIMEText(plain_text_content, 'plain', 'utf-8')
            message.attach(part1)

            part2 = MIMEText(html_content, 'html', 'utf-8')
            message.attach(part2)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send via Gmail API
            logger.info("Sending email via Gmail API...")
            send_message = self.service.users().messages().send(
                userId=sender,
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent successfully! Message ID: {send_message['id']}")
            return True

        except HttpError as error:
            logger.error(f"Gmail API HTTP error: {error}")
            if error.resp.status == 401:
                logger.error("Authentication failed. Try deleting token.pickle and re-authenticating")
            return False

        except Exception as e:
            logger.error(f"Error sending email via Gmail API: {e}")
            return False

    def send_digest(
        self,
        recipient: str,
        html_content: str,
        plain_text_content: str,
        article_count: int,
        subject_prefix: str = "Early Bird",
        date: Optional[str] = None
    ) -> bool:
        """
        Send daily digest email.

        Args:
            recipient: Recipient email address
            html_content: HTML email body
            plain_text_content: Plain text email body
            article_count: Number of articles in digest
            subject_prefix: Subject line prefix
            date: Date string (defaults to today)

        Returns:
            True if email sent successfully
        """
        if date is None:
            date = datetime.now().strftime("%B %d, %Y")

        # Build subject line
        subject = f"{subject_prefix}: {date} - {article_count} AI & Robotics Updates"

        # Send email
        return self.send_email(
            recipient=recipient,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text_content
        )

    def send_test_email(self, recipient: str) -> bool:
        """
        Send a test email to verify Gmail API configuration.

        Args:
            recipient: Recipient email address

        Returns:
            True if test email sent successfully
        """
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #667eea;">🐦 Early Bird Test Email</h1>
            <p>This is a test email from your Early Bird news aggregator.</p>
            <p>If you received this, your <strong>Gmail API</strong> configuration is working correctly!</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Sent via Gmail API at {datetime}
            </p>
        </body>
        </html>
        """.format(datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        plain_text = """
EARLY BIRD TEST EMAIL

This is a test email from your Early Bird news aggregator.

If you received this, your Gmail API configuration is working correctly!

---
Sent via Gmail API at {datetime}
        """.format(datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        subject = "Early Bird - Gmail API Test"

        logger.info("Sending test email via Gmail API...")
        return self.send_email(
            recipient=recipient,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text
        )

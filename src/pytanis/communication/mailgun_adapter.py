"""Mailgun adapter for the communication abstraction"""

from typing import Any

from structlog import get_logger

from pytanis.communication.base import BaseMailClient, EmailMessage
from pytanis.config import get_cfg
from pytanis.mailgun.mail import Mail, MailClient, Recipient

_logger = get_logger()


class MailgunAdapter(BaseMailClient):
    """Mailgun email client adapter

    This class wraps the existing Mailgun functionality to provide a consistent
    interface with other email providers.
    """

    def __init__(self, config: Any = None):
        """Initialize the Mailgun adapter

        Args:
            config: Configuration object (if None, will use get_cfg())
        """

        if config is None:
            config = get_cfg()
        self._client = MailClient(config=config)
        self._config = config

    def send_email(self, message: EmailMessage) -> str | None:
        """Send an email message using Mailgun"""
        try:
            # Convert to Mailgun format

            # Extract recipients
            if not message.to:
                msg = 'No recipients specified'
                raise ValueError(msg)

            # Create recipient objects for all recipients
            recipients = []
            for email in message.to:
                # Extract name from email if no metadata is provided
                name = email.split('@')[0]
                recipients.append(
                    Recipient(
                        name=name,
                        email=email,
                    )
                )

            # Create mail object with correct parameters
            mail = Mail(
                subject=message.subject,
                body=message.body,
                recipients=recipients,
            )

            # Send email using the correct method name
            responses, errors = self._client.send(mail)

            # Check for errors
            if errors:
                error_msgs = [f'{recipient.email}: {error!s}' for recipient, error in errors]
                _logger.error('Errors sending emails', errors=error_msgs)
                if not responses:
                    msg = f'All emails failed: {"; ".join(error_msgs)}'
                    raise OSError(msg)

            # Handle additional recipients as CC/BCC (not supported by current Mailgun implementation)
            if message.cc or message.bcc:
                _logger.warning(
                    'Mailgun adapter currently does not support CC/BCC recipients.',
                    cc=message.cc,
                    bcc=message.bcc,
                )

            # Return the first response ID if available
            if responses and hasattr(responses[0], 'json'):
                return responses[0].json().get('id')

            return None

        except Exception as e:
            msg = f'Error sending email via Mailgun: {e}'
            raise OSError(msg) from e

    def send_bulk_emails(self, messages: list[EmailMessage], rate_limit: int | None = None) -> list[str | None]:
        """Send multiple email messages

        Note: This implementation sends emails individually as the Mailgun client
        handles batching internally based on its batch_size configuration.
        """
        results = []

        # If rate limit is specified, override the client's wait time
        if rate_limit:
            original_batch_size = self._client.batch_size
            original_wait_time = self._client.wait_time
            self._client.batch_size = 1  # Send one at a time
            self._client.wait_time = int(1.0 / rate_limit)

        try:
            for i, message in enumerate(messages):
                try:
                    # For bulk sends, we could optimize by creating a single Mail object
                    # with all recipients if all messages have the same subject/body
                    msg_id = self.send_email(message)
                    results.append(msg_id)

                except Exception as e:
                    _logger.error('Failed to send email', error=str(e), index=i, to=message.to)
                    results.append(None)

        finally:
            # Restore original settings if we modified them
            if rate_limit:
                self._client.batch_size = original_batch_size
                self._client.wait_time = original_wait_time

        return results

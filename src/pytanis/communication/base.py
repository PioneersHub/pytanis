"""Base classes for communication abstraction"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from structlog import get_logger

_logger = get_logger()


@dataclass
class EmailMessage:
    """Standard email message representation"""

    to: list[str]
    subject: str
    body: str
    html_body: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    reply_to: str | None = None
    attachments: list[tuple[str, bytes]] | None = None  # (filename, content)
    headers: dict[str, str] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class Ticket:
    """Support ticket representation"""

    id: str | None
    subject: str
    description: str
    requester_email: str
    requester_name: str | None = None
    status: str = 'open'
    priority: str = 'normal'
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


@dataclass
class TicketComment:
    """Comment on a support ticket"""

    ticket_id: str
    body: str
    author_email: str
    author_name: str | None = None
    public: bool = True
    attachments: list[tuple[str, bytes]] | None = None


class BaseMailClient(ABC):
    """Abstract base class for email clients

    This class defines the interface for sending emails through various
    providers (e.g., SMTP, Mailgun, SendGrid, etc.).
    """

    @abstractmethod
    def send_email(self, message: EmailMessage) -> str | None:
        """Send an email message

        Args:
            message: The email message to send

        Returns:
            Message ID if available, None otherwise

        Raises:
            IOError: If there's an error sending the email
        """
        pass

    @abstractmethod
    def send_bulk_emails(self, messages: list[EmailMessage], rate_limit: int | None = None) -> list[str | None]:
        """Send multiple email messages

        Args:
            messages: List of email messages to send
            rate_limit: Maximum emails per second (None for no limit)

        Returns:
            List of message IDs (None for failures)

        Raises:
            IOError: If there's an error sending emails
        """
        pass

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate an email address format

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class BaseTicketClient(ABC):
    """Abstract base class for support ticket clients

    This class defines the interface for managing support tickets through
    various providers (e.g., HelpDesk, Zendesk, Freshdesk, etc.).
    """

    @abstractmethod
    def create_ticket(self, ticket: Ticket) -> str:
        """Create a new support ticket

        Args:
            ticket: The ticket to create

        Returns:
            The created ticket ID

        Raises:
            IOError: If there's an error creating the ticket
        """
        pass

    @abstractmethod
    def get_ticket(self, ticket_id: str) -> Ticket:
        """Get a ticket by ID

        Args:
            ticket_id: The ticket ID

        Returns:
            The ticket details

        Raises:
            KeyError: If the ticket does not exist
            IOError: If there's an error retrieving the ticket
        """
        pass

    @abstractmethod
    def update_ticket(self, ticket_id: str, updates: dict[str, Any]) -> None:
        """Update a ticket

        Args:
            ticket_id: The ticket ID
            updates: Dictionary of fields to update

        Raises:
            KeyError: If the ticket does not exist
            IOError: If there's an error updating the ticket
        """
        pass

    @abstractmethod
    def add_comment(self, comment: TicketComment) -> str:
        """Add a comment to a ticket

        Args:
            comment: The comment to add

        Returns:
            The comment ID

        Raises:
            KeyError: If the ticket does not exist
            IOError: If there's an error adding the comment
        """
        pass

    @abstractmethod
    def list_tickets(
        self, status: str | None = None, requester_email: str | None = None, limit: int = 100
    ) -> list[Ticket]:
        """List tickets with optional filtering

        Args:
            status: Filter by status (e.g., 'open', 'closed')
            requester_email: Filter by requester email
            limit: Maximum number of tickets to return

        Returns:
            List of tickets matching the criteria

        Raises:
            IOError: If there's an error listing tickets
        """
        pass

    @abstractmethod
    def close_ticket(self, ticket_id: str) -> None:
        """Close a ticket

        Args:
            ticket_id: The ticket ID

        Raises:
            KeyError: If the ticket does not exist
            IOError: If there's an error closing the ticket
        """
        pass

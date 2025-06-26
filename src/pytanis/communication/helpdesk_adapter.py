"""HelpDesk adapter for the communication abstraction"""

from typing import Any

from structlog import get_logger

from pytanis.communication.base import BaseMailClient, BaseTicketClient, EmailMessage, Ticket, TicketComment
from pytanis.config import get_cfg
from pytanis.helpdesk import HelpDeskClient, MailClient
from pytanis.helpdesk.mail import Mail, Recipient
from pytanis.helpdesk.models import Assignment, Id, Message, NewTicket, Requester

_logger = get_logger()


class HelpDeskMailAdapter(BaseMailClient):
    """HelpDesk email client adapter

    This class wraps the existing HelpDesk mail functionality to provide a
    consistent interface with other email providers.
    """

    def __init__(self, config: Any = None):
        """Initialize the HelpDesk mail adapter

        Args:
            config: Configuration object (if None, will use get_cfg())
        """
        if config is None:
            config = get_cfg()

        # Create HelpDeskClient first, then pass it to MailClient
        helpdesk_client = HelpDeskClient()
        self._client = MailClient(helpdesk_client=helpdesk_client)
        self._config = config

    def send_email(self, message: EmailMessage) -> str | None:
        """Send an email message using HelpDesk"""
        try:
            # Convert to HelpDesk format

            if not message.to:
                msg = 'No recipients specified'
                raise ValueError(msg)

            # Create recipient objects for all recipients
            recipients = []
            for email in message.to:
                recipient = Recipient(
                    name=email.split('@')[0],  # Use email prefix as name
                    email=email,
                )
                recipients.append(recipient)

            # Get team_id and agent_id from config (with defaults)
            team_id = getattr(self._config, 'helpdesk_team_id', 'default_team')
            agent_id = getattr(self._config, 'helpdesk_agent_id', 'default_agent')

            # Create mail object with required fields
            mail = Mail(
                subject=message.subject,
                text=message.body or message.html_body or '',
                team_id=team_id,
                agent_id=agent_id,
                recipients=recipients,
                status='solved',  # Default status
            )

            # Send email (dry_run=False to actually send)
            tickets, errors = self._client.send(mail, dry_run=False)

            # Log any errors
            if errors:
                for recipient, error in errors:
                    _logger.error('Failed to send to recipient', recipient=recipient.email, error=str(error))

            # Handle CC recipients warning
            if message.cc:
                _logger.warning(
                    'HelpDesk adapter does not support CC recipients. CC recipients ignored.',
                    cc=message.cc,
                )

            # Return the first ticket ID if successful
            if tickets and tickets[0][1]:
                # Access ID via dict since Ticket model uses extra='allow'
                ticket_dict = tickets[0][1].model_dump()
                return str(ticket_dict.get('ID', ''))
            return None

        except Exception as e:
            msg = f'Error sending email via HelpDesk: {e}'
            raise OSError(msg) from e

    def send_bulk_emails(self, messages: list[EmailMessage], rate_limit: int | None = None) -> list[str | None]:
        """Send multiple email messages"""
        # The HelpDesk MailClient handles batching internally
        # We'll create a single Mail object with all recipients for efficiency
        try:
            if not messages:
                return []

            all_recipients = []
            # Use the first message as template, assuming all have same content
            template_message = messages[0]

            for message in messages:
                if not message.to:
                    continue

                for email in message.to:
                    recipient = Recipient(
                        name=email.split('@')[0],  # Use email prefix as name
                        email=email,
                    )
                    all_recipients.append(recipient)

            if not all_recipients:
                return []

            # Get team_id and agent_id from config (with defaults)
            team_id = getattr(self._config, 'helpdesk_team_id', 'default_team')
            agent_id = getattr(self._config, 'helpdesk_agent_id', 'default_agent')

            # Create a single mail object with all recipients
            mail = Mail(
                subject=template_message.subject,
                text=template_message.body or template_message.html_body or '',
                team_id=team_id,
                agent_id=agent_id,
                recipients=all_recipients,
                status='solved',  # Default status
            )

            # Configure rate limiting if specified
            if rate_limit:
                self._client.batch_size = rate_limit

            # Send emails (dry_run=False to actually send)
            tickets, errors = self._client.send(mail, dry_run=False)

            # Log any errors
            if errors:
                for recipient, error in errors:
                    _logger.error('Failed to send to recipient', recipient=recipient.email, error=str(error))

            # Create result list matching input messages
            results: list[str | None] = []
            ticket_map = {ticket[0].email: ticket[1] for ticket in tickets if ticket[1]}

            for message in messages:
                if message.to and message.to[0] in ticket_map:
                    # Access ID via dict since Ticket model uses extra='allow'
                    ticket = ticket_map[message.to[0]]
                    ticket_dict = ticket.model_dump()
                    results.append(str(ticket_dict.get('ID', '')))
                else:
                    results.append(None)

            return results

        except Exception as e:
            msg = f'Error sending bulk emails via HelpDesk: {e}'
            raise OSError(msg) from e


class HelpDeskTicketAdapter(BaseTicketClient):
    """HelpDesk ticket client adapter

    This class wraps the existing HelpDesk client to provide a consistent
    interface with other ticket providers.
    """

    def __init__(self, config: Any = None):
        """Initialize the HelpDesk ticket adapter

        Args:
            config: Configuration object (if None, will use get_cfg())
        """

        if config is None:
            config = get_cfg()
        self._client = HelpDeskClient()
        self._config = config

    def create_ticket(self, ticket: Ticket) -> str:
        """Create a new support ticket"""
        try:
            # Create requester object
            requester = Requester(
                email=ticket.requester_email,
                name=ticket.requester_name or ticket.requester_email.split('@')[0],
            )

            # Create message object
            message = Message(text=ticket.description)

            # Get team_id and agent_id from config (with defaults)
            team_id = getattr(self._config, 'helpdesk_team_id', 'default_team')
            agent_id = getattr(self._config, 'helpdesk_agent_id', 'default_agent')

            # Create assignment if we have team and agent IDs
            assignment = None
            team_ids = None
            if team_id and agent_id:
                assignment = Assignment(
                    team=Id(ID=team_id),
                    agent=Id(ID=agent_id),
                )
                team_ids = [team_id]

            # Convert to HelpDesk format
            new_ticket = NewTicket(
                subject=ticket.subject,
                message=message,
                requester=requester,
                status=ticket.status or 'open',
                assignment=assignment,
                teamIDs=team_ids,
            )

            # Create ticket
            result = self._client.create_ticket(new_ticket)

            # Extract ticket ID from result
            if isinstance(result, dict) and 'ID' in result:
                return str(result['ID'])
            return str(result)

        except Exception as e:
            msg = f'Error creating ticket: {e}'
            raise OSError(msg) from e

    def get_ticket(self, ticket_id: str) -> Ticket:
        """Get a ticket by ID"""
        # HelpDesk client doesn't have a get_ticket method in the current implementation
        msg = 'HelpDesk adapter does not support getting tickets yet'
        raise NotImplementedError(msg)

    def update_ticket(self, ticket_id: str, updates: dict[str, Any]) -> None:
        """Update a ticket"""
        # HelpDesk client doesn't have an update_ticket method in the current implementation
        msg = 'HelpDesk adapter does not support updating tickets yet'
        raise NotImplementedError(msg)

    def add_comment(self, comment: TicketComment) -> str:
        """Add a comment to a ticket"""
        # HelpDesk client doesn't have an add_comment method in the current implementation
        msg = 'HelpDesk adapter does not support adding comments yet'
        raise NotImplementedError(msg)

    def list_tickets(
        self, status: str | None = None, requester_email: str | None = None, limit: int = 100
    ) -> list[Ticket]:
        """List tickets with optional filtering"""
        # HelpDesk client doesn't have a list_tickets method in the current implementation
        msg = 'HelpDesk adapter does not support listing tickets yet'
        raise NotImplementedError(msg)

    def close_ticket(self, ticket_id: str) -> None:
        """Close a ticket"""
        # HelpDesk client doesn't have a close_ticket method in the current implementation
        msg = 'HelpDesk adapter does not support closing tickets yet'
        raise NotImplementedError(msg)

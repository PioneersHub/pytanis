"""Functionality around mailing

ToDo:
    * add logging where appropriate
    * Find out why `extra=Extra.allow` causes mypy to fail. Seems like a bug in pydantic.
    * Sending mails is quite slow, so using `tqdm` to show feedback to the current progress would be nice
"""

import time
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, model_validator
from structlog import get_logger
from tqdm.auto import tqdm

from pytanis.helpdesk.client import HelpDeskClient
from pytanis.helpdesk.models import Assignment, Id, Message, NewTicket, Requester, Ticket

_logger = get_logger()


class MetaData(BaseModel):
    """Additional, arbitrary metadata provided by the user like for template filling"""

    model_config = ConfigDict(extra='allow')


class Recipient(BaseModel):
    """Details about the recipient

    Use the `data` field to store additional information
    """

    name: str
    email: str
    address_as: str | None = None  # could be the first name
    data: MetaData | None = None

    @model_validator(mode='after')
    def fill_address_as(self):
        if self.address_as is None:
            self.address_as = self.name
        return self


class Mail(BaseModel):
    """Mail template

    Use the `data` field to store additional information

    You can use the typical [Format String Syntax] and the objects `recipient` and `mail`
    to access metadata to complement the template, e.g.:

    ```
    Hello {recipient.address_as},

    We hope it's ok to address you your first name rather than using your full name being {recipient.name}.
    Have you read the email's subject '{mail.subject}'? How is your work right now at {recipient.data.company}?

    Cheers!
    ```

    [Format String Syntax]: https://docs.python.org/3/library/string.html#formatstrings
    """

    subject: str
    team_id: str
    agent_id: str
    text: str
    status: str = 'solved'  # ToDo: Reconsider this!
    recipients: list[Recipient]
    data: MetaData | None = None


class MailClient:
    """Mail client for mass mails over HelpDesk"""

    batch_size: int = 10  # n messages are a batch
    wait_time: int = 20  # wait time after eacht batch before next

    def __init__(self, helpdesk_client: HelpDeskClient | None = None):
        if helpdesk_client is None:
            helpdesk_client = HelpDeskClient()
        self._helpdesk_client = helpdesk_client
        self.dry_run: Callable[[NewTicket], None] = self.print_new_ticket

    @staticmethod
    def _create_ticket(mail: Mail, recipient: Recipient) -> NewTicket:
        message = Message(text=mail.text)
        requester = Requester(name=recipient.name, email=recipient.email)
        team_id, agent_id = Id(ID=mail.team_id), Id(ID=mail.agent_id)
        assignment = Assignment(team=team_id, agent=agent_id)
        ticket = NewTicket(
            requester=requester,
            message=message,
            subject=mail.subject,
            assignment=assignment,
            status=mail.status,
            teamIDs=[mail.team_id],
        )
        return ticket

    @staticmethod
    def print_new_ticket(ticket: NewTicket):
        """Default action in a dry-run. Mainly for making sure you sent what you mean!

        Overwrite it by assigning to self.dry_run another function

        ToDo: Make this function nice, maybe use the `rich` library even
        """
        print('#' * 40)  # noqa: T201
        print(f'Recipient: {ticket.requester.name} <{ticket.requester.email}>')  # noqa: T201
        print(f'Subject: {ticket.subject}')  # noqa: T201
        print(f'{ticket.message.text}')  # noqa: T201

    def send(
        self, mail: Mail, *, dry_run: bool = True
    ) -> tuple[list[tuple[Recipient, Ticket | None]], list[tuple[Recipient, Exception]]]:
        """Send a mail to all recipients using HelpDesk"""
        errors = []
        tickets = []
        for idx, recipient in enumerate(tqdm(mail.recipients), start=1):
            recip_mail = mail.model_copy()
            try:
                recip_mail.subject = mail.subject.format(recipient=recipient, mail=mail)
                # be aware here that the body might reference to subject line, so it must be filled already
                recip_mail.text = recip_mail.text.format(recipient=recipient, mail=recip_mail)
                ticket = self._create_ticket(recip_mail, recipient)
                if dry_run:
                    self.print_new_ticket(ticket)
                    resp_ticket = None
                else:
                    resp = self._helpdesk_client.create_ticket(ticket)
                    resp_ticket = Ticket.model_validate(resp)
            except Exception as e:
                errors.append((recipient, e))
            else:
                tickets.append((recipient, resp_ticket))
            if (idx % self.batch_size == 0) and not dry_run:
                time.sleep(self.wait_time)

        return tickets, errors

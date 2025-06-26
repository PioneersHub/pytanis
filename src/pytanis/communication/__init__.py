"""Communication abstraction layer for Pytanis

This module provides abstract base classes and implementations for sending
emails and managing support tickets through various providers.
"""

from pytanis.communication.base import BaseMailClient, BaseTicketClient, EmailMessage, Ticket, TicketComment

__all__ = ['BaseMailClient', 'BaseTicketClient', 'EmailMessage', 'Ticket', 'TicketComment']

# Optional imports for adapters
try:
    from pytanis.communication.mailgun_adapter import MailgunAdapter  # noqa: F401

    __all__.append('MailgunAdapter')
except ImportError:
    pass  # MailgunAdapter not available

try:
    from pytanis.communication.helpdesk_adapter import HelpDeskMailAdapter, HelpDeskTicketAdapter  # noqa: F401

    __all__.extend(['HelpDeskMailAdapter', 'HelpDeskTicketAdapter'])
except ImportError:
    pass  # HelpDesk adapters not available

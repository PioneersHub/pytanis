"""Factory functions for creating storage and communication clients"""

from structlog import get_logger

from pytanis.communication import HelpDeskMailAdapter, HelpDeskTicketAdapter, MailgunAdapter
from pytanis.communication.base import BaseMailClient, BaseTicketClient
from pytanis.config import Config, get_cfg

_logger = get_logger()


def get_mail_client(config: Config | None = None) -> BaseMailClient:
    """Get a mail client based on configuration

    Args:
        config: Configuration object (if None, will use get_cfg())

    Returns:
        A mail client instance

    Raises:
        ValueError: If no email provider is configured or if it's not supported
        ImportError: If the provider's dependencies are not installed
    """
    if config is None:
        config = get_cfg()

    # Get communication configuration
    comm_cfg = config.Communication
    if comm_cfg is None or comm_cfg.email_provider is None:
        # Check legacy configuration
        if config.Mailgun is not None and config.Mailgun.token is not None:
            _logger.info('Using Mailgun from legacy configuration')
            provider = 'mailgun'
        elif config.HelpDesk is not None and config.HelpDesk.token is not None:
            _logger.info('Using HelpDesk from legacy configuration')
            provider = 'helpdesk'
        else:
            msg = 'No email provider configured'
            raise ValueError(msg)
    else:
        provider = comm_cfg.email_provider.lower()

    if provider == 'mailgun':
        return MailgunAdapter(config=config)

    elif provider == 'helpdesk':
        return HelpDeskMailAdapter(config=config)
    else:
        msg = f'Unknown email provider: {provider}'
        raise ValueError(msg)


def get_ticket_client(config: Config | None = None) -> BaseTicketClient:
    """Get a ticket client based on configuration

    Args:
        config: Configuration object (if None, will use get_cfg())

    Returns:
        A ticket client instance

    Raises:
        ValueError: If no ticket provider is configured or if it's not supported
        ImportError: If the provider's dependencies are not installed
    """
    if config is None:
        config = get_cfg()

    # Get communication configuration
    comm_cfg = config.Communication
    if comm_cfg is None or comm_cfg.ticket_provider is None:
        # Check legacy configuration
        if config.HelpDesk is not None and config.HelpDesk.token is not None:
            _logger.info('Using HelpDesk from legacy configuration')
            provider = 'helpdesk'
        else:
            msg = 'No ticket provider configured'
            raise ValueError(msg)
    else:
        provider = comm_cfg.ticket_provider.lower()

    if provider != 'helpdesk':
        msg = f'Unknown ticket provider: {provider}'
        raise ValueError(msg)

    else:
        return HelpDeskTicketAdapter(config=config)

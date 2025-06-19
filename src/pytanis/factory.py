"""Factory functions for creating storage and communication clients"""

from structlog import get_logger

from pytanis.communication.base import BaseMailClient, BaseTicketClient
from pytanis.config import Config, get_cfg
from pytanis.storage.base import BaseSpreadsheetClient

_logger = get_logger()


def get_storage_client(config: Config | None = None) -> BaseSpreadsheetClient:
    """Get a storage client based on configuration

    Args:
        config: Configuration object (if None, will use get_cfg())

    Returns:
        A storage client instance

    Raises:
        ValueError: If the configured provider is not supported
        ImportError: If the provider's dependencies are not installed
    """
    if config is None:
        config = get_cfg()

    # Get storage configuration
    storage_cfg = config.Storage
    if storage_cfg is None:
        # Default to local storage
        from pytanis.storage.local import LocalFileClient

        _logger.info('No storage configuration found, defaulting to local storage')
        return LocalFileClient()

    provider = storage_cfg.provider.lower()

    if provider == 'local':
        from pytanis.storage.local import LocalFileClient

        base_path = storage_cfg.local_path or '.'
        return LocalFileClient(base_path=base_path)

    elif provider == 'google':
        try:
            from pytanis.storage.google import GoogleSheetsStorageClient
        except ImportError as e:
            raise ImportError(
                'Google Sheets dependencies not installed. Install with: pip install pytanis[google]'
            ) from e
        return GoogleSheetsStorageClient(config=config)

    else:
        raise ValueError(f'Unknown storage provider: {provider}')


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
            raise ValueError('No email provider configured')
    else:
        provider = comm_cfg.email_provider.lower()

    if provider == 'mailgun':
        try:
            from pytanis.communication.mailgun_adapter import MailgunAdapter
        except ImportError as e:
            raise ImportError('Mailgun dependencies not installed. Install with: pip install pytanis[mailgun]') from e
        return MailgunAdapter(config=config)

    elif provider == 'helpdesk':
        try:
            from pytanis.communication.helpdesk_adapter import HelpDeskMailAdapter
        except ImportError as e:
            raise ImportError('HelpDesk dependencies not installed. Install with: pip install pytanis[helpdesk]') from e
        return HelpDeskMailAdapter(config=config)

    else:
        raise ValueError(f'Unknown email provider: {provider}')


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
            raise ValueError('No ticket provider configured')
    else:
        provider = comm_cfg.ticket_provider.lower()

    if provider == 'helpdesk':
        try:
            from pytanis.communication.helpdesk_adapter import HelpDeskTicketAdapter
        except ImportError as e:
            raise ImportError('HelpDesk dependencies not installed. Install with: pip install pytanis[helpdesk]') from e
        return HelpDeskTicketAdapter(config=config)

    else:
        raise ValueError(f'Unknown ticket provider: {provider}')

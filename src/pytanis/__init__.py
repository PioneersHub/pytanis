from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

import structlog.stdlib

from pytanis.config import get_cfg
from pytanis.factory import get_mail_client, get_ticket_client
from pytanis.pretalx import (
    PretalxClient,
    SimpleTalk,
    get_confirmed_talks_as_json,  # For backward compatibility
    get_talks_as_json,
    save_confirmed_talks_to_json,  # For backward compatibility
    save_talks_to_json,
    talks_to_json,
)

# Lazy imports for optional components
if TYPE_CHECKING:
    from pytanis.google import GSheetsClient
    from pytanis.helpdesk import HelpDeskClient

try:
    __version__ = version('pytanis')
except PackageNotFoundError:  # pragma: no cover
    __version__ = 'unknown'
finally:
    del version, PackageNotFoundError

__all__ = [
    'GSheetsClient',
    'HelpDeskClient',
    'PretalxClient',
    'SimpleTalk',
    '__version__',
    'get_cfg',
    'get_confirmed_talks_as_json',  # For backward compatibility
    'get_mail_client',
    'get_talks_as_json',
    'get_ticket_client',
    'save_confirmed_talks_to_json',  # For backward compatibility
    'save_talks_to_json',
    'talks_to_json',
]


# Lazy loading implementation
def __getattr__(name):
    """Lazy load optional components"""
    if name == 'GSheetsClient':
        try:
            from pytanis.google import GSheetsClient  # noqa: PLC0415

            return GSheetsClient
        except ImportError as e:
            msg = 'Google Sheets dependencies not installed. Install with: pip install pytanis[google]'
            raise ImportError(msg) from e
    elif name == 'HelpDeskClient':
        try:
            from pytanis.helpdesk import HelpDeskClient  # noqa: PLC0415

            return HelpDeskClient
        except ImportError as e:
            msg = 'HelpDesk dependencies not installed. Install with: pip install pytanis[helpdesk]'
            raise ImportError(msg) from e
    msg = f"module '{__name__}' has no attribute '{name}'"
    raise AttributeError(msg)


# transform structlog into a logging-friendly package
# use `logging.basicConfig(level=logging.INFO, stream=sys.stdout)` as usual
# taken from https://www.structlog.org/en/stable/standard-library.html#rendering-within-structlog
structlog.configure(
    processors=[
        # If log level is too low, abort pipeline and throw away log entry.
        structlog.stdlib.filter_by_level,
        # Add the name of the logger to event dict.
        structlog.stdlib.add_logger_name,
        # Add log level to event dict.
        structlog.stdlib.add_log_level,
        # Perform %-style formatting.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add a timestamp in ISO 8601 format.
        structlog.processors.TimeStamper(fmt='iso'),
        # If the "stack_info" key in the event dict is true, remove it and
        # render the current stack trace in the "stack" key.
        structlog.processors.StackInfoRenderer(),
        # If the "exc_info" key in the event dict is either true or a
        # sys.exc_info() tuple, remove "exc_info" and render the exception
        # with traceback into the "exception" key.
        structlog.processors.format_exc_info,
        # If some value is in bytes, decode it to a unicode str.
        structlog.processors.UnicodeDecoder(),
        # Add callsite parameters.
        structlog.processors.CallsiteParameterAdder({
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        }),
        # Render the final event dict as JSON.
        structlog.processors.JSONRenderer(),
    ],
    # `wrapper_class` is the bound logger that you get back from
    # get_logger(). This one imitates the API of `logging.Logger`.
    wrapper_class=structlog.stdlib.BoundLogger,
    # `logger_factory` is used to create wrapped loggers that are used for
    # OUTPUT. This one returns a `logging.Logger`. The final value (a JSON
    # string) from the final processor (`JSONRenderer`) will be passed to
    # the method of the same name as that you've called on the bound logger.
    logger_factory=structlog.stdlib.LoggerFactory(),
    # Effectively freeze configuration after creating the first bound
    # logger.
    cache_logger_on_first_use=True,
)

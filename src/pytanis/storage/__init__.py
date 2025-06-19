"""Storage abstraction layer for Pytanis

This module provides abstract base classes and implementations for storing
and retrieving conference data in various formats and backends.
"""

from pytanis.storage.base import BaseSpreadsheetClient, BaseStorageClient
from pytanis.storage.local import LocalFileClient

__all__ = ['BaseSpreadsheetClient', 'BaseStorageClient', 'LocalFileClient']

# Optional imports
try:
    from pytanis.storage.google import GoogleSheetsStorageClient

    __all__.append('GoogleSheetsStorageClient')
except ImportError:
    pass  # GoogleSheetsStorageClient not available

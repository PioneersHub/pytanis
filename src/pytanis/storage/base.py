"""Base classes for storage abstraction"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
from structlog import get_logger

_logger = get_logger()


class BaseStorageClient(ABC):
    """Abstract base class for storage clients

    This class defines the interface for reading and writing data to various
    storage backends (e.g., local files, cloud storage, databases).
    """

    @abstractmethod
    def read(self, key: str) -> Any:
        """Read data from storage

        Args:
            key: The storage key/path to read from

        Returns:
            The data stored at the given key

        Raises:
            KeyError: If the key does not exist
            IOError: If there's an error reading the data
        """
        pass

    @abstractmethod
    def write(self, key: str, data: Any) -> None:
        """Write data to storage

        Args:
            key: The storage key/path to write to
            data: The data to store

        Raises:
            IOError: If there's an error writing the data
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in storage

        Args:
            key: The storage key/path to check

        Returns:
            True if the key exists, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete data from storage

        Args:
            key: The storage key/path to delete

        Raises:
            KeyError: If the key does not exist
            IOError: If there's an error deleting the data
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: str = '') -> list[str]:
        """List all keys in storage with optional prefix filtering

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of keys matching the prefix
        """
        pass


class BaseSpreadsheetClient(ABC):
    """Abstract base class for spreadsheet-like storage

    This class defines the interface for working with tabular data in a
    spreadsheet-like format, supporting multiple worksheets/tabs.
    """

    @abstractmethod
    def read_sheet(self, spreadsheet_id: str, sheet_name: str | None = None) -> pd.DataFrame:
        """Read a sheet as a pandas DataFrame

        Args:
            spreadsheet_id: The identifier for the spreadsheet
            sheet_name: The name of the sheet to read (None for default/first sheet)

        Returns:
            The sheet data as a DataFrame

        Raises:
            KeyError: If the spreadsheet or sheet does not exist
            IOError: If there's an error reading the data
        """
        pass

    @abstractmethod
    def write_sheet(
        self, spreadsheet_id: str, data: pd.DataFrame, sheet_name: str | None = None, *, overwrite: bool = True
    ) -> None:
        """Write a pandas DataFrame to a sheet

        Args:
            spreadsheet_id: The identifier for the spreadsheet
            data: The DataFrame to write
            sheet_name: The name of the sheet to write to
            overwrite: Whether to overwrite existing data

        Raises:
            IOError: If there's an error writing the data
        """
        pass

    @abstractmethod
    def create_spreadsheet(self, name: str) -> str:
        """Create a new spreadsheet

        Args:
            name: The name for the new spreadsheet

        Returns:
            The identifier for the created spreadsheet

        Raises:
            IOError: If there's an error creating the spreadsheet
        """
        pass

    @abstractmethod
    def list_sheets(self, spreadsheet_id: str) -> list[str]:
        """List all sheets in a spreadsheet

        Args:
            spreadsheet_id: The identifier for the spreadsheet

        Returns:
            List of sheet names

        Raises:
            KeyError: If the spreadsheet does not exist
            IOError: If there's an error listing sheets
        """
        pass

    @abstractmethod
    def delete_sheet(self, spreadsheet_id: str, sheet_name: str) -> None:
        """Delete a sheet from a spreadsheet

        Args:
            spreadsheet_id: The identifier for the spreadsheet
            sheet_name: The name of the sheet to delete

        Raises:
            KeyError: If the spreadsheet or sheet does not exist
            IOError: If there's an error deleting the sheet
        """
        pass

    def read_all_sheets(self, spreadsheet_id: str) -> dict[str, pd.DataFrame]:
        """Read all sheets from a spreadsheet

        Args:
            spreadsheet_id: The identifier for the spreadsheet

        Returns:
            Dictionary mapping sheet names to DataFrames

        Raises:
            KeyError: If the spreadsheet does not exist
            IOError: If there's an error reading the data
        """
        sheets = self.list_sheets(spreadsheet_id)
        return {sheet: self.read_sheet(spreadsheet_id, sheet) for sheet in sheets}

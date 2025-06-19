"""Google Sheets storage implementation"""

from typing import TYPE_CHECKING, Any

import pandas as pd
from structlog import get_logger

from pytanis.storage.base import BaseSpreadsheetClient

if TYPE_CHECKING:
    from pytanis.google import GSheetsClient

_logger = get_logger()


class GoogleSheetsStorageClient(BaseSpreadsheetClient):
    """Google Sheets storage adapter implementing the storage interface

    This class wraps the existing GSheetsClient to provide a consistent
    interface with other storage backends.
    """

    def __init__(self, config: Any = None):
        """Initialize the Google Sheets storage client

        Args:
            config: Configuration object (if None, will use get_cfg())
        """
        # Lazy import to avoid dependency issues
        try:
            from pytanis.google import GSheetsClient  # noqa: PLC0415
        except ImportError as e:
            raise ImportError(
                'Google Sheets dependencies not installed. Install with: pip install pytanis[google]'
            ) from e

        self._client = GSheetsClient(config=config)

    def read_sheet(self, spreadsheet_id: str, sheet_name: str | None = None) -> pd.DataFrame:
        """Read a sheet as a pandas DataFrame"""
        try:
            worksheet = self._client.get_worksheet(spreadsheet_id, sheet_name)
            return self._client.worksheet_as_df(worksheet)
        except Exception as e:
            if 'not found' in str(e).lower():
                raise KeyError(f'Spreadsheet or sheet not found: {spreadsheet_id}/{sheet_name}')
            raise OSError(f'Error reading sheet: {e}') from e

    def write_sheet(
        self, spreadsheet_id: str, data: pd.DataFrame, sheet_name: str | None = None, *, overwrite: bool = True
    ) -> None:
        """Write a pandas DataFrame to a sheet"""
        try:
            worksheet = self._client.get_worksheet(spreadsheet_id, sheet_name)
            self._client.df_to_worksheet(data, worksheet, overwrite=overwrite)
        except Exception as e:
            raise OSError(f'Error writing sheet: {e}') from e

    def create_spreadsheet(self, name: str) -> str:
        """Create a new spreadsheet"""
        try:
            spreadsheet = self._client.create_spreadsheet(name)
            return spreadsheet.id
        except Exception as e:
            raise OSError(f'Error creating spreadsheet: {e}') from e

    def list_sheets(self, spreadsheet_id: str) -> list[str]:
        """List all sheets in a spreadsheet"""
        try:
            spreadsheet = self._client.get_spreadsheet(spreadsheet_id)
            return [ws.title for ws in spreadsheet.worksheets()]
        except Exception as e:
            if 'not found' in str(e).lower():
                raise KeyError(f'Spreadsheet not found: {spreadsheet_id}')
            raise OSError(f'Error listing sheets: {e}') from e

    def delete_sheet(self, spreadsheet_id: str, sheet_name: str) -> None:
        """Delete a sheet from a spreadsheet"""
        try:
            spreadsheet = self._client.get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            spreadsheet.del_worksheet(worksheet)
        except Exception as e:
            if 'not found' in str(e).lower():
                raise KeyError(f'Sheet not found: {sheet_name}')
            raise OSError(f'Error deleting sheet: {e}') from e

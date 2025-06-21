"""Local file storage implementation"""

import json
from pathlib import Path
from typing import Any

import pandas as pd
from structlog import get_logger

from pytanis.storage.base import BaseSpreadsheetClient, BaseStorageClient

_logger = get_logger()


class LocalFileClient(BaseStorageClient, BaseSpreadsheetClient):
    """Local file storage client supporting various formats

    This client stores data as local files and supports:
    - JSON files for general data storage
    - CSV/Excel files for spreadsheet-like data
    """

    def __init__(self, base_path: Path | str = '.'):
        """Initialize the local file client

        Args:
            base_path: Base directory for storing files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """Get the full path for a given key"""
        path = self.base_path / key
        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    # BaseStorageClient implementation

    def read(self, key: str) -> Any:
        """Read data from a JSON file"""
        path = self._get_path(key)
        if not path.exists():
            raise KeyError(f'File not found: {key}')

        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise OSError(f'Error reading file {key}: {e}') from e

    def write(self, key: str, data: Any) -> None:
        """Write data to a JSON file"""
        path = self._get_path(key)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            raise OSError(f'Error writing file {key}: {e}') from e

    def exists(self, key: str) -> bool:
        """Check if a file exists"""
        return self._get_path(key).exists()

    def delete(self, key: str) -> None:
        """Delete a file"""
        path = self._get_path(key)
        if not path.exists():
            raise KeyError(f'File not found: {key}')

        try:
            path.unlink()
        except Exception as e:
            raise OSError(f'Error deleting file {key}: {e}') from e

    def list_keys(self, prefix: str = '') -> list[str]:
        """List all files with optional prefix filtering"""
        pattern = f'{prefix}*' if prefix else '*'
        paths = self.base_path.rglob(pattern)
        return [str(p.relative_to(self.base_path)) for p in paths if p.is_file()]

    # BaseSpreadsheetClient implementation

    def _get_spreadsheet_path(self, spreadsheet_id: str, extension: str = '.xlsx') -> Path:
        """Get the path for a spreadsheet file"""
        if not spreadsheet_id.endswith(('.xlsx', '.csv')):
            spreadsheet_id = f'{spreadsheet_id}{extension}'
        return self._get_path(spreadsheet_id)

    def read_sheet(self, spreadsheet_id: str, sheet_name: str | None = None) -> pd.DataFrame:
        """Read a sheet from a CSV or Excel file"""
        path = self._get_spreadsheet_path(spreadsheet_id)

        if not path.exists():
            raise KeyError(f'Spreadsheet not found: {spreadsheet_id}')

        try:
            if path.suffix == '.csv':
                if sheet_name is not None:
                    _logger.warning('Sheet name ignored for CSV files', sheet_name=sheet_name)
                return pd.read_csv(path)
            else:  # Excel
                # Always specify sheet_name to ensure we get a DataFrame, not a dict
                sheet_to_read: str | int = sheet_name if sheet_name is not None else 0
                return pd.read_excel(path, sheet_name=sheet_to_read)
        except Exception as e:
            raise OSError(f'Error reading spreadsheet {spreadsheet_id}: {e}') from e

    def write_sheet(
        self, spreadsheet_id: str, data: pd.DataFrame, sheet_name: str | None = None, *, overwrite: bool = True
    ) -> None:
        """Write a DataFrame to a CSV or Excel file"""
        path = self._get_spreadsheet_path(spreadsheet_id)

        try:
            if path.suffix == '.csv':
                if sheet_name is not None:
                    _logger.warning('Sheet name ignored for CSV files', sheet_name=sheet_name)
                data.to_csv(path, index=False)
            elif path.exists() and not overwrite:
                # Append to existing Excel file
                with pd.ExcelWriter(path, mode='a', if_sheet_exists='replace') as writer:
                    data.to_excel(writer, sheet_name=sheet_name or 'Sheet1', index=False)
            else:
                # Create new or overwrite
                with pd.ExcelWriter(path, mode='w') as writer:
                    data.to_excel(writer, sheet_name=sheet_name or 'Sheet1', index=False)
        except Exception as e:
            raise OSError(f'Error writing spreadsheet {spreadsheet_id}: {e}') from e

    def create_spreadsheet(self, name: str) -> str:
        """Create a new empty spreadsheet"""
        if not name.endswith(('.xlsx', '.csv')):
            name = f'{name}.xlsx'

        path = self._get_path(name)
        if path.exists():
            raise OSError(f'Spreadsheet already exists: {name}')

        # Create empty file
        if path.suffix == '.csv':
            pd.DataFrame().to_csv(path, index=False)
        else:
            with pd.ExcelWriter(path, mode='w') as writer:
                pd.DataFrame().to_excel(writer, sheet_name='Sheet1', index=False)

        return name

    def list_sheets(self, spreadsheet_id: str) -> list[str]:
        """List all sheets in a spreadsheet"""
        path = self._get_spreadsheet_path(spreadsheet_id)

        if not path.exists():
            raise KeyError(f'Spreadsheet not found: {spreadsheet_id}')

        if path.suffix == '.csv':
            return ['default']  # CSV files don't have multiple sheets

        try:
            # For Excel files, read sheet names
            excel_file = pd.ExcelFile(path)
            # Convert all sheet names to strings
            return [str(name) for name in excel_file.sheet_names]
        except Exception as e:
            raise OSError(f'Error listing sheets in {spreadsheet_id}: {e}') from e

    def delete_sheet(self, spreadsheet_id: str, sheet_name: str) -> None:
        """Delete a sheet from a spreadsheet"""
        path = self._get_spreadsheet_path(spreadsheet_id)

        if not path.exists():
            raise KeyError(f'Spreadsheet not found: {spreadsheet_id}')

        if path.suffix == '.csv':
            raise OSError('Cannot delete sheets from CSV files')

        try:
            # Read all sheets except the one to delete
            excel_file = pd.ExcelFile(path)
            sheets_to_keep = {
                name: pd.read_excel(excel_file, sheet_name=name)
                for name in excel_file.sheet_names
                if name != sheet_name
            }

            if sheet_name not in excel_file.sheet_names:
                raise KeyError(f'Sheet not found: {sheet_name}')

            if not sheets_to_keep:
                raise OSError('Cannot delete the last sheet in a spreadsheet')

            # Write back remaining sheets
            with pd.ExcelWriter(path, mode='w') as writer:
                for name, df in sheets_to_keep.items():
                    df.to_excel(writer, sheet_name=str(name), index=False)

        except Exception as e:
            if isinstance(e, KeyError | OSError):
                raise
            raise OSError(f'Error deleting sheet {sheet_name} from {spreadsheet_id}: {e}') from e

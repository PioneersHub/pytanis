# Migration Summary: Making HelpDesk and Google Sheets Optional

## What Was Done

### 1. Storage Abstraction Layer
- Created `src/pytanis/storage/` with abstract base classes
- Implemented `LocalFileClient` for CSV/Excel file storage
- Created `GoogleSheetsStorageClient` adapter for existing functionality
- All storage providers implement the same interface

### 2. Communication Abstraction Layer
- Created `src/pytanis/communication/` with abstract base classes
- Created adapters for existing Mailgun and HelpDesk clients
- Defined standard `EmailMessage` and `Ticket` data classes

### 3. Optional Dependencies
- Updated `pyproject.toml` to move dependencies to extras:
  - `pytanis[google]` - Google Sheets support
  - `pytanis[helpdesk]` - HelpDesk support
  - `pytanis[mailgun]` - Mailgun support
  - `pytanis[jupyter]` - Jupyter notebooks
  - `pytanis[optimization]` - Schedule optimization
  - `pytanis[all]` - Everything

### 4. Configuration Updates
- Made Google, HelpDesk, and Mailgun sections optional in Config
- Added new Storage and Communication configuration sections
- Backward compatible - old configs still work

### 5. Lazy Loading
- `GSheetsClient` and `HelpDeskClient` are now lazy-loaded
- Clear error messages when dependencies are missing
- Maintains backward compatibility

### 6. Factory Functions
- `get_storage_client()` - Returns appropriate storage backend
- `get_mail_client()` - Returns appropriate email client
- `get_ticket_client()` - Returns appropriate ticket client

## Benefits

1. **Reduced Dependencies**: Core installation is much lighter
2. **Flexibility**: Easy to switch between storage/communication providers
3. **Testing**: Can use local storage for tests instead of Google Sheets
4. **Extensibility**: Easy to add new providers
5. **Backward Compatible**: Existing code continues to work

## Migration Path

For existing users:
```bash
# If using all features
pip install pytanis[all]

# Or only what you need
pip install pytanis[google,mailgun]
```

New code can use the abstraction:
```python
from pytanis import get_storage_client

storage = get_storage_client()  # Uses config to determine provider
df = storage.read_sheet('data', 'Sheet1')
```

Old code still works:
```python
from pytanis import GSheetsClient  # Still works if pytanis[google] installed
client = GSheetsClient()
```

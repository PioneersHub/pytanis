# Optional Components

Starting with version 0.8.0, Pytanis has been refactored to make external dependencies optional. This allows you to install only the components you need, reducing the overall dependency footprint.

## Installation

### Core Installation
The core installation includes only the essential dependencies:
```bash
pip install pytanis
```

This gives you:
- Pretalx client for conference management
- Local file storage (CSV/Excel)
- Core utilities and configuration

### Optional Components

Install additional components as needed:

```bash
# Google Sheets support
pip install pytanis[google]

# HelpDesk support
pip install pytanis[helpdesk]

# Mailgun support
pip install pytanis[mailgun]

# Jupyter notebooks and visualization
pip install pytanis[jupyter]

# Schedule optimization
pip install pytanis[optimization]

# Everything
pip install pytanis[all]
```

## Storage Abstraction

Pytanis now provides a storage abstraction layer that allows you to choose between different storage backends.

### Configuration

Configure your storage provider in `config.toml`:

```toml
[Storage]
provider = "local"  # or "google"
local_path = "./data"  # for local storage

[Google]  # Only needed if using Google storage
client_secret_json = "client_secret.json"
token_json = "token.json"
```

### Using the Storage API

```python
from pytanis import get_storage_client
import pandas as pd

# Get storage client based on configuration
storage = get_storage_client()

# Create a DataFrame
df = pd.DataFrame({'name': ['Alice', 'Bob'], 'score': [95, 87]})

# Write to storage (works with both local and Google)
storage.write_sheet('my_data', df, sheet_name='results')

# Read from storage
df_read = storage.read_sheet('my_data', 'results')

# List available sheets
sheets = storage.list_sheets('my_data')
```

### Local Storage

When using local storage:
- Files are stored as Excel (.xlsx) or CSV files
- Spreadsheet IDs map to filenames
- Multiple sheets are supported for Excel files

### Google Sheets Storage

When using Google Sheets:
- Requires `pytanis[google]` installation
- Uses the same API as local storage
- Spreadsheet IDs are Google Sheets IDs

## Communication Abstraction

Pytanis provides abstraction for email and ticket systems.

### Configuration

```toml
[Communication]
email_provider = "mailgun"  # or "helpdesk"
ticket_provider = "helpdesk"

[Mailgun]  # If using Mailgun
token = "your-token"
from_address = "noreply@example.com"

[HelpDesk]  # If using HelpDesk
account = "your-account"
entity_id = "your-entity"
token = "your-token"
```

### Using the Communication API

```python
from pytanis import get_mail_client
from pytanis.communication import EmailMessage

# Get mail client based on configuration
mail_client = get_mail_client()

# Create and send an email
message = EmailMessage(
    to=['recipient@example.com'],
    subject='Conference Update',
    body='Your talk has been accepted!',
    html_body='<p>Your talk has been accepted!</p>'
)

message_id = mail_client.send_email(message)
```

## Backward Compatibility

The original APIs (`GSheetsClient`, `HelpDeskClient`) are still available and work as before. They are now lazy-loaded, meaning dependencies are only required when you actually use them.

```python
# This still works but requires pytanis[google]
from pytanis import GSheetsClient
client = GSheetsClient()

# This still works but requires pytanis[helpdesk]
from pytanis import HelpDeskClient
client = HelpDeskClient()
```

## Migration Guide

### For Existing Projects

1. **Update your installation**:
   ```bash
   # If you use all features
   pip install pytanis[all]

   # Or install only what you need
   pip install pytanis[google,mailgun]
   ```

2. **Update your configuration** (optional):
   Add the new sections to use the abstraction layer:
   ```toml
   [Storage]
   provider = "google"  # Keep using Google Sheets

   [Communication]
   email_provider = "mailgun"  # Keep using Mailgun
   ```

3. **Update your code** (optional):
   You can continue using the old APIs or migrate to the new abstraction:
   ```python
   # Old way (still works)
   from pytanis import GSheetsClient
   client = GSheetsClient()

   # New way (recommended)
   from pytanis import get_storage_client
   storage = get_storage_client()
   ```

### For New Projects

1. Install only what you need
2. Use the new abstraction APIs
3. Configure providers in `config.toml`

## Benefits

- **Lighter installations**: Only install dependencies you actually use
- **Flexibility**: Easy to switch between providers
- **Testing**: Use local storage for tests, Google Sheets for production
- **Future-proof**: Easy to add new providers without changing your code

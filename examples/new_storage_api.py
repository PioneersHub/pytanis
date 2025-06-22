#!/usr/bin/env python3
"""
Example showing the new storage API with optional dependencies.

This example demonstrates how to use the new storage abstraction
layer that allows switching between local files and Google Sheets.
"""

import tempfile
from pathlib import Path

from pytanis import get_cfg, get_storage_client
from pytanis.config import Config


def example_google_storage():
    """Example using Google Sheets storage (requires pytanis[google])"""
    try:
        # Create config with Google storage
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as tmp:
            temp_config_path = tmp.name

        config = Config(
            cfg_path=temp_config_path,  # Use secure temp file
            Pretalx={'api_token': 'dummy'},  # Required but not used here
            Google={'client_secret_json': 'path/to/client_secret.json', 'token_json': 'path/to/token.json'},
        )

        # Clean up temp file
        Path(temp_config_path).unlink(missing_ok=True)

        # Get storage client
        storage = get_storage_client(config)
        print('Google Sheets storage client created')

        # Usage is the same as local storage!
        # storage.write_sheet('spreadsheet_id', df)
        # df = storage.read_sheet('spreadsheet_id', 'Sheet1')

        # Example of what you can do with the storage client:
        _ = storage  # Mark as intentionally unused in this demo

    except ImportError as e:
        print(f'Google Sheets not available: {e}')
        print('Install with: pip install pytanis[google]')


def example_from_config_file():
    """Example loading storage configuration from file"""
    # Assuming config.toml contains:
    # [Storage]
    # provider = "local"
    # local_path = "./conference_data"

    config = get_cfg()
    storage = get_storage_client(config)

    print(f'Storage provider: {config.Storage.provider}')
    # Use storage client...
    _ = storage  # Mark as intentionally unused in this demo


if __name__ == '__main__':
    print('\n=== Google Storage Example ===')
    example_google_storage()

    print('\n=== Config File Example ===')
    # example_from_config_file()  # Uncomment if you have a config file

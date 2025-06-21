"""Fixtures for the unit tests of Pytanis"""

import os
from pathlib import Path
from shutil import copy

import pytest

from pytanis.config import PYTANIS_CFG_PATH, PYTANIS_ENV, get_cfg
from pytanis.pretalx.client import PretalxClient

__location__ = Path(__file__).parent


def has_valid_pretalx_token():
    """Check if we have a valid Pretalx API token available.

    Checks in order:
    1. PRETALX_API_TOKEN environment variable
    2. Local ~/.pytanis/config.toml file

    Returns:
        bool: True if a token is available, False otherwise
    """
    # Check environment variable first (highest priority)
    if os.getenv('PRETALX_API_TOKEN'):
        return True

    # Check local config file
    try:
        cfg = get_cfg()
        return bool(cfg.Pretalx.api_token)
    except Exception:
        # Config file doesn't exist or is invalid
        return False


@pytest.fixture
def tmp_config(tmp_path):
    cfg_path = tmp_path / Path(PYTANIS_CFG_PATH)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)

    copy(__location__ / Path('cfgs/config.toml'), cfg_path)
    copy(__location__ / Path('cfgs/client_secret.json'), cfg_path.parent)

    old_env = os.environ.get(PYTANIS_ENV)
    os.environ[PYTANIS_ENV] = str(cfg_path)
    yield
    if old_env is None:
        del os.environ[PYTANIS_ENV]
    else:
        os.environ[PYTANIS_ENV] = old_env


@pytest.fixture
def pretalx_client():
    return PretalxClient()


@pytest.fixture
def authenticated_client(tmp_config):
    """PretalxClient that uses test config with authentication.

    This fixture ensures the client uses the test configuration
    which includes a dummy API token. Use this for testing
    endpoints that require authentication.
    """
    return PretalxClient()

"""Fixtures for the unit tests of Pytanis"""

import os
from pathlib import Path
from shutil import copy

import pytest

from pytanis.config import PYTANIS_CFG_PATH, PYTANIS_ENV
from pytanis.pretalx.client import PretalxClient

__location__ = Path(__file__).parent


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

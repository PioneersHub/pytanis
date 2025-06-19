"""Handling the configuration"""

import os
from pathlib import Path

import tomli
from pydantic import BaseModel, FilePath, field_validator
from pydantic_core.core_schema import ValidationInfo

PYTANIS_ENV: str = 'PYTANIS_CONFIG'
"""Name of the environment variable to look up the path for the config"""
PYTANIS_CFG_PATH: str = '.pytanis/config.toml'
"""Path within $HOME to the configuration file of Pytanis"""


class GoogleCfg(BaseModel):
    """Configuration related to the Google API"""

    client_secret_json: Path | None = None
    token_json: Path | None = None
    service_user_authentication: bool = False


class HelpDeskCfg(BaseModel):
    """Configuration related to the HelpDesk API"""

    account: str | None = None
    entity_id: str | None = None
    token: str | None = None


class MailgunCfg(BaseModel):
    """Configuration related to the Mailgun API"""

    token: str | None = None
    from_address: str | None = None
    reply_to: str | None = None


class PretalxCfg(BaseModel):
    """Configuration related to the Pretalx API"""

    api_token: str | None = None
    api_version: str = 'v1'


class Config(BaseModel):
    """Main configuration object"""

    cfg_path: FilePath

    Pretalx: PretalxCfg
    Google: GoogleCfg
    HelpDesk: HelpDeskCfg
    Mailgun: MailgunCfg

    @field_validator('Google')
    @classmethod
    def convert_json_path(cls, v: GoogleCfg, info: ValidationInfo) -> GoogleCfg:
        def make_rel_path_abs(entry):
            if entry is not None and not entry.is_absolute():
                entry = info.data['cfg_path'].parent / entry
            return entry

        v.client_secret_json = make_rel_path_abs(v.client_secret_json)
        v.token_json = make_rel_path_abs(v.token_json)

        return v


def get_cfg_file() -> Path:
    """Determines the path of the config file"""
    path_str = os.environ.get(PYTANIS_ENV, None)
    path = Path.home() / Path(PYTANIS_CFG_PATH) if path_str is None else Path(path_str)
    return path


def get_cfg() -> Config:
    """Returns the configuration as an object"""
    cfg_path = get_cfg_file()
    with open(cfg_path, 'rb') as fh:
        cfg_dict = tomli.load(fh)
    # add config path to later resolve relative paths of config values
    cfg_dict['cfg_path'] = cfg_path
    return Config.model_validate(cfg_dict)

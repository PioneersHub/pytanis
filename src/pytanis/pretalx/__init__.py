"""Functionality around the Pretalx API"""

from pytanis.pretalx.client import PretalxClient
from pytanis.pretalx.models import SimpleTalk
from pytanis.pretalx.utils import (
    get_confirmed_talks_as_json,  # For backward compatibility
    get_talks_as_json,
    reviews_as_df,
    save_confirmed_talks_to_json,  # For backward compatibility
    save_talks_to_json,
    speakers_as_df,
    subs_as_df,
    talks_to_json,
)

__all__ = [
    'PretalxClient',
    'SimpleTalk',
    'get_confirmed_talks_as_json',  # For backward compatibility
    'get_talks_as_json',
    'reviews_as_df',
    'save_confirmed_talks_to_json',  # For backward compatibility
    'save_talks_to_json',
    'speakers_as_df',
    'subs_as_df',
    'talks_to_json',
]

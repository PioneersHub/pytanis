"""These tests will only run if you have set up an Pretalx Account"""

import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import from conftest
sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import has_valid_pretalx_token

from .test_config import (
    EVENT_DATE_FROM,
    EVENT_SLUG,
    VALID_ROOM_ID,
    VALID_ROOM_NAME,
    VALID_SUBMISSION_CODE,
    VALID_SUBMISSION_TYPE,
)

# Mark for auth-required tests - these endpoints need special permissions
requires_auth = pytest.mark.skipif(
    not has_valid_pretalx_token(), reason='Requires valid authentication (PRETALX_API_TOKEN env var or local config)'
)


@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_events_endpoint(pretalx_client):
    count, all_events = pretalx_client.events()
    assert count == len(list(all_events))


@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_event_endpoint(pretalx_client):
    event = pretalx_client.event(EVENT_SLUG)
    assert event.date_from == EVENT_DATE_FROM


@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_submissions_endpoint(pretalx_client):
    count, subs = pretalx_client.submissions(EVENT_SLUG)
    assert count == len(list(subs))


@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_submission_endpoint(pretalx_client):
    sub = pretalx_client.submission(EVENT_SLUG, VALID_SUBMISSION_CODE)
    assert sub.submission_type.en == VALID_SUBMISSION_TYPE


@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_talks_endpoint(pretalx_client):
    count, talks = pretalx_client.talks(EVENT_SLUG)
    assert count == len(list(talks))


# ToDo: Add check for single speaker too


@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_speakers_endpoint(pretalx_client):
    count, speakers = pretalx_client.speakers(EVENT_SLUG)
    assert count == len(list(speakers))


# ToDo: Add check for single speaker too


@requires_auth
@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_reviews_endpoint(pretalx_client):
    """Test reviews endpoint (requires authentication)."""
    count, reviews = pretalx_client.reviews(EVENT_SLUG)
    assert count == len(list(reviews))


# ToDo: Add check for single review too


@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_rooms_endpoint(pretalx_client):
    count, rooms = pretalx_client.rooms(EVENT_SLUG)
    assert count == len(list(rooms))


@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_room_endpoint(pretalx_client):
    room = pretalx_client.room(EVENT_SLUG, VALID_ROOM_ID)
    assert room.name.en == VALID_ROOM_NAME


@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_questions_endpoint(pretalx_client):
    count, questions = pretalx_client.questions(EVENT_SLUG)
    assert count == len(list(questions))


# ToDo: Add check for single question too


@requires_auth
@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_answers_endpoint(pretalx_client):
    """Test answers endpoint (requires authentication)."""
    count, answers = pretalx_client.answers(EVENT_SLUG)
    assert count == len(list(answers))


# ToDo: Add check for single answer too


@requires_auth
@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')
def test_tags_endpoint(pretalx_client):
    """Test tags endpoint (requires authentication)."""
    count, tags = pretalx_client.tags(EVENT_SLUG)
    assert count == len(list(tags))


# ToDo: Add check for single tag too

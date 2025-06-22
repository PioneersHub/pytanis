"""Integration tests that require a Pretalx API token.

These tests validate all Pydantic models against live API data.
They require authentication via PRETALX_API_TOKEN env var or local config.
"""

import os
from pathlib import Path

import pytest
import tomli

from pytanis import PretalxClient
from pytanis.config import get_cfg

# Skip all tests in this file if on GitHub or no authentication available
pytestmark = pytest.mark.skipif(
    os.getenv('GITHUB'),
    reason='Skipped on GitHub CI or when no authentication available',
)

# Load test configuration
test_config_path = Path(__file__).parent.parent / 'test_config.toml'
if test_config_path.exists():
    with open(test_config_path, 'rb') as f:
        test_config = tomli.load(f)
        default_event_slug = test_config.get('test', {}).get('event_slug')

# Use event slug from environment variable or test configuration
TEST_EVENT_SLUG = os.getenv('PRETALX_TEST_EVENT', default_event_slug)


@pytest.fixture(scope='module')
def client():
    """Provide fallback on env variable for CI/CD."""
    config = get_cfg()
    if not config.Pretalx.api_token:
        config.Pretalx.api_token = os.getenv('PRETALX_API_TOKEN')
    return PretalxClient(config=config)


class TestAllPretalxModels:
    """Test all Pretalx Pydantic models with live API data."""

    @pytest.mark.integration
    def test_event_model(self, client):
        """Test the Event model."""
        _event = client.event(TEST_EVENT_SLUG)

    @pytest.mark.integration
    def test_submission_models(
        self,
        client,
    ):
        """Test Submission and related models."""
        _count, _submissions = client.submissions(TEST_EVENT_SLUG, params={'state': 'confirmed', 'limit': 2})

    @pytest.mark.integration
    def test_talk_models(self, client):
        """Test Talk and related models."""
        _count, _talks = client.talks(TEST_EVENT_SLUG, params={'limit': 2})

    @pytest.mark.integration
    def test_speaker_models(self, client):
        """Test Speaker and SpeakerAvailability models."""
        _count, _speakers = client.speakers(TEST_EVENT_SLUG, params={'limit': 2})

    @pytest.mark.integration
    def test_room_models(self, client):
        """Test Room and RoomAvailability models."""
        _count, _rooms = client.rooms(TEST_EVENT_SLUG)

    @pytest.mark.integration
    def test_question_models(self, client):
        """Test Question and Option models."""
        _count, _questions = client.questions(TEST_EVENT_SLUG)

    @pytest.mark.integration
    def test_tag_model(self, client):
        """Test Tag model."""
        _count, _tags = client.tags(TEST_EVENT_SLUG)

    @pytest.mark.integration
    def test_review_models(self, client):
        """Test Review and User models."""
        _count, _reviews = client.reviews(TEST_EVENT_SLUG, params={'limit': 2})

    @pytest.mark.integration
    def test_answer_model(self, client):
        """Test Answer model in detail."""
        _count, _answers = client.answers(TEST_EVENT_SLUG, params={'limit': 2})

"""Integration tests for Pretalx API and Pydantic model validation.

These tests use live Pretalx API data to validate all Pydantic models.
Data is fetched but not stored, used only for validation purposes.
"""

import os

import pytest

from pytanis.pretalx import PretalxClient
from pytanis.pretalx.models import (
    Answer,
    AnswerQuestionRef,
    Speaker,
    SpeakerAvailability,
    Submission,
    SubmissionSpeaker,
)

# Use a public Pretalx instance for testing
# This should be a conference that has public data available
TEST_EVENT_SLUG = 'pyconde-pydata-2025'  # Update this to a current/accessible event
PUBLIC_PRETALX_URL = 'https://pretalx.com/api'  # Default public instance


@pytest.fixture(scope='module')
def integration_client():
    """Create a PretalxClient for integration testing.

    This uses environment variables if available, otherwise falls back to public API.
    """
    # Check if we have API credentials in environment
    api_token = os.getenv('PRETALX_API_TOKEN')

    # Create a minimal config for testing
    from pathlib import Path  # noqa: PLC0415

    from pytanis.config import Config, PretalxCfg  # noqa: PLC0415

    # Use a dummy config path
    config = Config(
        cfg_path=Path.home() / '.pytanis' / 'config.toml',  # This path doesn't need to exist
        Pretalx=PretalxCfg(api_token=api_token),
    )

    return PretalxClient(config=config)


@pytest.fixture(scope='module')
def test_event_slug():
    """Get the event slug to use for testing."""
    return os.getenv('PRETALX_TEST_EVENT', TEST_EVENT_SLUG)


class TestPretalxModels:
    """Test all Pretalx Pydantic models with live API data."""

    @pytest.mark.integration
    def test_submission_model(self, integration_client, test_event_slug):
        """Test the Submission model with live data."""
        try:
            _count, submissions = integration_client.submissions(
                test_event_slug, params={'state': 'confirmed', 'limit': 5}
            )
            submissions_list = list(submissions)

            if not submissions_list:
                pytest.skip('No confirmed submissions found')

            for submission in submissions_list:
                # Validate the model was properly constructed
                assert isinstance(submission, Submission)
                assert submission.code is not None
                assert submission.title is not None
                assert submission.state is not None
                assert submission.submission_type is not None

                # Test speakers
                assert isinstance(submission.speakers, list)
                for speaker in submission.speakers:
                    assert isinstance(speaker, SubmissionSpeaker)
                    assert speaker.code is not None
                    assert speaker.name is not None

                # Test answers if present
                if submission.answers:
                    assert isinstance(submission.answers, list)
                    for answer in submission.answers:
                        assert isinstance(answer, Answer)
                        assert isinstance(answer.question, AnswerQuestionRef)

                # Validate model serialization
                submission_dict = submission.model_dump()
                assert isinstance(submission_dict, dict)

                # Validate model can be reconstructed
                Submission.model_validate(submission_dict)
        except Exception as e:
            if '404' in str(e):
                pytest.skip(f'Event not found: {test_event_slug}')
            raise

    @pytest.mark.integration
    def test_speaker_model(self, integration_client, test_event_slug):
        """Test the Speaker model with live data."""
        try:
            _count, speakers = integration_client.speakers(test_event_slug, params={'limit': 5})
            speakers_list = list(speakers)

            if not speakers_list:
                pytest.skip('No speakers found')

            for speaker in speakers_list:
                # Validate the model was properly constructed
                assert isinstance(speaker, Speaker)
                assert speaker.code is not None
                assert speaker.name is not None

                # Test availabilities if present
                if speaker.availabilities:
                    assert isinstance(speaker.availabilities, list)
                    for availability in speaker.availabilities:
                        assert isinstance(availability, SpeakerAvailability)
                        assert availability.start is not None
                        assert availability.end is not None

                # Test answers if present
                if speaker.answers:
                    assert isinstance(speaker.answers, list)
                    for answer in speaker.answers:
                        assert isinstance(answer, Answer)

                # Validate model serialization
                speaker_dict = speaker.model_dump()
                assert isinstance(speaker_dict, dict)

                # Validate model can be reconstructed
                Speaker.model_validate(speaker_dict)
        except Exception as e:
            if '404' in str(e):
                pytest.skip(f'Event not found: {test_event_slug}')
            raise


class TestPretalxEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.integration
    def test_nonexistent_event(self, integration_client):
        """Test handling of non-existent event."""
        with pytest.raises(Exception):
            integration_client.event('this-event-does-not-exist-12345')

    @pytest.mark.integration
    def test_empty_collections(self, integration_client, test_event_slug):
        """Test handling of empty collections."""
        try:
            # Try to get submissions with a filter that likely returns nothing
            _count, submissions = integration_client.submissions(
                test_event_slug, params={'state': 'deleted', 'limit': 1}
            )

            # Should handle empty results gracefully
            submissions_list = list(submissions)
            assert isinstance(submissions_list, list)
            # It's OK if it's empty
        except Exception as e:
            if '404' in str(e):
                pytest.skip('Event not found')
            raise


# Marker for running integration tests
pytest.mark.integration = pytest.mark.skipif(
    os.getenv('SKIP_INTEGRATION_TESTS', 'false').lower() == 'true', reason='Integration tests skipped'
)

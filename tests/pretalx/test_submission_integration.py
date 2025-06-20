"""Comprehensive integration tests for Pretalx Submission model.

These tests validate that submissions from the Pretalx API can be successfully
loaded into the Submission Pydantic model, including all nested models and fields.
Tests use live API data with the new expand functionality.
"""

import os

import pytest
import structlog

from pytanis.pretalx import PretalxClient
from pytanis.pretalx.models import (
    Answer,
    AnswerQuestionRef,
    MultiLingualStr,
    Resource,
    Slot,
    State,
    Submission,
    SubmissionSpeaker,
    Talk,
)

# Configure structlog for human-readable test output
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt='%H:%M:%S'),
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@pytest.fixture(scope='module')
def test_client():
    """Create a PretalxClient for testing."""
    # Use environment variable if available, otherwise public API
    api_token = os.getenv('PRETALX_API_TOKEN')
    client = PretalxClient()
    if api_token:
        client._config.Pretalx.api_token = api_token
    return client


@pytest.fixture(scope='module')
def test_event():
    """Get the test event slug."""
    return os.getenv('PRETALX_TEST_EVENT', 'pyconde-pydata-2025')


class TestSubmissionModel:
    """Comprehensive tests for the Submission model with live API data."""

    @pytest.mark.integration
    def test_submission_model_with_full_expansion(self, test_client, test_event):
        """Test submission model with default expand parameters."""
        # Fetch submissions with default expansion (should include answers, speakers, etc.)
        count, submissions = test_client.submissions(test_event, params={'limit': 3})
        submissions_list = list(submissions)

        assert count > 0, 'Should have at least one submission'
        assert len(submissions_list) > 0, 'Should have retrieved submissions'

        for submission in submissions_list:
            # Basic validation
            assert isinstance(submission, Submission)
            self._validate_submission_fields(submission)

            # Validate expansion worked correctly
            self._validate_expanded_fields(submission)

            # Test serialization
            submission_dict = submission.model_dump()
            assert isinstance(submission_dict, dict)

            # Test reconstruction
            reconstructed = Submission.model_validate(submission_dict)
            assert reconstructed.code == submission.code
            assert reconstructed.title == submission.title

    @pytest.mark.integration
    def test_submission_model_without_expansion(self, test_client, test_event):  # noqa: PLR6301
        """Test submission model without expand parameter for backward compatibility."""
        # Explicitly disable expansion
        _count, submissions = test_client.submissions(
            test_event,
            params={'limit': 2, 'expand': ''},  # Empty expand parameter
        )
        submissions_list = list(submissions)

        if submissions_list:
            submission = submissions_list[0]
            assert isinstance(submission, Submission)

            # Basic fields should still work
            assert submission.code is not None
            assert submission.title is not None
            assert submission.state is not None

            # Speakers should still be expanded (backward compatibility)
            if submission.speakers:
                assert isinstance(submission.speakers[0], SubmissionSpeaker)
                assert hasattr(submission.speakers[0], 'name')

    @pytest.mark.integration
    def test_submission_field_validation(self, test_client, test_event):  # noqa: PLR6301
        """Test all submission fields are properly validated."""
        _count, submissions = test_client.submissions(test_event, params={'limit': 5})
        submissions_list = list(submissions)

        assert len(submissions_list) > 0, 'Need at least one submission for testing'

        for submission in submissions_list:
            # Required fields
            assert isinstance(submission.code, str) and submission.code
            assert isinstance(submission.title, str) and submission.title
            assert isinstance(submission.speakers, list)
            assert isinstance(submission.submission_type, MultiLingualStr)
            assert isinstance(submission.submission_type_id, int)
            assert isinstance(submission.state, State)
            assert isinstance(submission.abstract, str)
            assert isinstance(submission.description, str)
            assert isinstance(submission.do_not_record, bool)
            assert isinstance(submission.is_featured, bool)

            # Optional fields
            if submission.created is not None:
                from datetime import datetime  # noqa: PLC0415

                assert isinstance(submission.created, datetime)

            if submission.track is not None:
                assert isinstance(submission.track, MultiLingualStr)

            if submission.track_id is not None:
                assert isinstance(submission.track_id, int)

            if submission.duration is not None:
                assert isinstance(submission.duration, int)

            if submission.slot is not None:
                assert isinstance(submission.slot, Slot)

            if submission.image is not None:
                assert isinstance(submission.image, str)

            if submission.tags is not None:
                assert isinstance(submission.tags, list)
                for tag in submission.tags:
                    assert isinstance(tag, str)

            if submission.tag_ids is not None:
                assert isinstance(submission.tag_ids, list)
                for tag_id in submission.tag_ids:
                    assert isinstance(tag_id, int)

    @pytest.mark.integration
    def test_submission_nested_models(self, test_client, test_event):  # noqa: PLR6301
        """Test nested models within submissions."""
        _count, submissions = test_client.submissions(test_event, params={'limit': 3})
        submissions_list = list(submissions)

        for submission in submissions_list:
            # Test speakers
            assert isinstance(submission.speakers, list)
            for speaker in submission.speakers:
                assert isinstance(speaker, SubmissionSpeaker)
                assert isinstance(speaker.code, str)
                assert isinstance(speaker.name, str)
                if speaker.biography is not None:
                    assert isinstance(speaker.biography, str)
                if speaker.avatar is not None:
                    assert isinstance(speaker.avatar, str)
                if speaker.email is not None:
                    assert isinstance(speaker.email, str)

            # Test answers if present
            if submission.answers is not None:
                assert isinstance(submission.answers, list)
                for answer in submission.answers:
                    assert isinstance(answer, Answer)
                    assert isinstance(answer.id, int)
                    assert isinstance(answer.answer, str)
                    assert isinstance(answer.question, AnswerQuestionRef)
                    assert isinstance(answer.question.id, int)
                    assert isinstance(answer.question.question, MultiLingualStr)
                    if answer.answer_file is not None:
                        assert isinstance(answer.answer_file, str)
                    assert isinstance(answer.options, list)

            # Test resources
            assert isinstance(submission.resources, list)
            for resource in submission.resources:
                assert isinstance(resource, Resource)
                assert isinstance(resource.resource, str)
                assert isinstance(resource.description, str)

            # Test slot if present
            if submission.slot is not None:
                assert isinstance(submission.slot, Slot)
                if submission.slot.start is not None:
                    from datetime import datetime  # noqa: PLC0415

                    assert isinstance(submission.slot.start, datetime)
                if submission.slot.end is not None:
                    from datetime import datetime  # noqa: PLC0415

                    assert isinstance(submission.slot.end, datetime)
                if submission.slot.room is not None:
                    assert isinstance(submission.slot.room, MultiLingualStr)
                if submission.slot.room_id is not None:
                    assert isinstance(submission.slot.room_id, int)

    @pytest.mark.integration
    def test_submission_different_states(self, test_client, test_event):
        """Test submissions in different states."""
        states_to_test = ['confirmed', 'accepted', 'submitted']

        for state in states_to_test:
            try:
                _count, submissions = test_client.submissions(test_event, params={'state': state, 'limit': 2})
                submissions_list = list(submissions)

                if submissions_list:
                    for submission in submissions_list:
                        assert isinstance(submission, Submission)
                        assert submission.state.value == state
                        self._validate_submission_fields(submission)

            except Exception as e:
                # Some states might not have submissions
                if '404' not in str(e):
                    raise

    @pytest.mark.integration
    def test_submission_serialization(self, test_client, test_event):  # noqa: PLR6301
        """Test model serialization and deserialization."""
        _count, submissions = test_client.submissions(test_event, params={'limit': 1})
        submissions_list = list(submissions)

        assert len(submissions_list) > 0, 'Need at least one submission'

        submission = submissions_list[0]

        # Test model_dump
        submission_dict = submission.model_dump()
        assert isinstance(submission_dict, dict)
        assert submission_dict['code'] == submission.code
        assert submission_dict['title'] == submission.title

        # Test model_dump with exclude_none
        submission_dict_no_none = submission.model_dump(exclude_none=True)
        for _key, value in submission_dict_no_none.items():
            assert value is not None

        # Test model_dump_json
        submission_json = submission.model_dump_json()
        assert isinstance(submission_json, str)

        # Test reconstruction from dict
        reconstructed = Submission.model_validate(submission_dict)
        assert reconstructed.code == submission.code
        assert reconstructed.title == submission.title
        assert len(reconstructed.speakers) == len(submission.speakers)

        # Test reconstruction from JSON
        import json  # noqa: PLC0415

        reconstructed_from_json = Submission.model_validate(json.loads(submission_json))
        assert reconstructed_from_json.code == submission.code

    @pytest.mark.integration
    def test_submission_edge_cases(self, test_client, test_event):  # noqa: PLR6301
        """Test edge cases and special scenarios."""
        _count, submissions = test_client.submissions(test_event, params={'limit': 10})
        submissions_list = list(submissions)

        # Track different scenarios found
        found_no_speakers = False
        found_no_track = False
        found_no_answers = False
        found_multiple_speakers = False

        for submission in submissions_list:
            # Submission with no speakers
            if not submission.speakers:
                found_no_speakers = True
                assert submission.speakers == []

            # Submission with no track
            if submission.track is None:
                found_no_track = True
                assert submission.track_id is None or submission.track_id == 0

            # Submission with no answers
            if submission.answers is None or len(submission.answers) == 0:
                found_no_answers = True

            # Submission with multiple speakers
            if len(submission.speakers) > 1:
                found_multiple_speakers = True
                # Validate each speaker
                for speaker in submission.speakers:
                    assert isinstance(speaker, SubmissionSpeaker)
                    assert speaker.code is not None
                    assert speaker.name is not None

        # Log what edge cases were found (not all might exist in test data)
        logger.info(
            'edge_cases_summary',
            message='Edge cases found in test data',
            no_speakers=found_no_speakers,
            no_track=found_no_track,
            no_answers=found_no_answers,
            multiple_speakers=found_multiple_speakers,
        )

    @pytest.mark.integration
    def test_talk_model_inheritance(self, test_client, test_event):
        """Test that Talk model properly inherits from Submission."""
        try:
            _count, talks = test_client.talks(test_event, params={'limit': 2})
            talks_list = list(talks)

            if talks_list:
                for talk in talks_list:
                    # Talk should be instance of both Talk and Submission
                    assert isinstance(talk, Talk)
                    assert isinstance(talk, Submission)

                    # All submission fields should be available
                    self._validate_submission_fields(talk)

                    # Test serialization as Talk
                    talk_dict = talk.model_dump()
                    reconstructed_talk = Talk.model_validate(talk_dict)
                    assert reconstructed_talk.code == talk.code

        except Exception as e:
            if '404' in str(e):
                # Talks endpoint might not be available, try submissions
                _count, submissions = test_client.submissions(test_event, params={'limit': 2})
                submissions_list = list(submissions)

                if submissions_list:
                    # Convert to Talk objects
                    for submission in submissions_list:
                        talk_dict = submission.model_dump()
                        talk = Talk.model_validate(talk_dict)
                        assert isinstance(talk, Talk)
                        assert isinstance(talk, Submission)

    def _validate_submission_fields(self, submission: Submission) -> None:  # noqa: PLR6301
        """Helper to validate basic submission fields."""
        assert submission.code is not None
        assert submission.title is not None
        assert submission.state is not None
        assert submission.submission_type is not None
        assert submission.submission_type_id is not None
        assert submission.abstract is not None
        assert submission.description is not None
        assert isinstance(submission.speakers, list)
        assert isinstance(submission.do_not_record, bool)
        assert isinstance(submission.is_featured, bool)

    def _validate_expanded_fields(self, submission: Submission) -> None:  # noqa: PLR6301
        """Helper to validate fields that should be expanded."""
        # Speakers should be objects, not IDs
        if submission.speakers:
            speaker = submission.speakers[0]
            assert isinstance(speaker, SubmissionSpeaker)
            assert hasattr(speaker, 'code')
            assert hasattr(speaker, 'name')
            assert isinstance(speaker.code, str)
            assert isinstance(speaker.name, str)

        # Submission type should be MultiLingualStr, not ID
        assert isinstance(submission.submission_type, MultiLingualStr)
        if submission.submission_type.en:
            assert isinstance(submission.submission_type.en, str)

        # Track should be MultiLingualStr if present
        if submission.track is not None:
            assert isinstance(submission.track, MultiLingualStr)

        # Answers should be objects if present
        if submission.answers is not None and len(submission.answers) > 0:
            answer = submission.answers[0]
            assert isinstance(answer, Answer)
            assert hasattr(answer, 'id')
            assert hasattr(answer, 'answer')
            assert hasattr(answer, 'question')
            assert isinstance(answer.question, AnswerQuestionRef)


@pytest.mark.integration
class TestSubmissionAPIPerformance:
    """Test performance aspects of submission retrieval."""

    def test_no_individual_answer_calls(self, test_client, test_event, caplog):  # noqa: PLR6301
        """Verify no individual API calls are made for answers when using expand."""
        import logging  # noqa: PLC0415

        # Set logging to capture warnings
        caplog.set_level(logging.WARNING)

        # Fetch submissions with default expansion
        _count, submissions = test_client.submissions(test_event, params={'limit': 2})
        submissions_list = list(submissions)

        # Check logs for warnings about answer IDs
        answer_warnings = [
            record for record in caplog.records if 'answer IDs instead of expanded answers' in record.message
        ]

        # With proper expansion, there should be no warnings about answer IDs
        assert len(answer_warnings) == 0, (
            f'Found {len(answer_warnings)} warnings about unexpanded answers. '
            'This suggests the expand parameter is not working correctly.'
        )

        # Verify answers are properly expanded if present
        for submission in submissions_list:
            if submission.answers:
                for answer in submission.answers:
                    assert isinstance(answer, Answer)
                    assert not isinstance(answer, int), 'Answer should be object, not ID'

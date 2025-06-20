"""Integration tests that require a Pretalx API token.

These tests validate all Pydantic models against live API data.
They require PRETALX_API_TOKEN to be set in the environment.
"""

import os

import pytest

from pytanis import PretalxClient
from pytanis.config import Config, PretalxCfg
from pytanis.pretalx.models import (
    Answer,
    AnswerQuestionRef,
    Event,
    Me,
    MultiLingualStr,
    Option,
    Question,
    Resource,
    Review,
    Room,
    RoomAvailability,
    Slot,
    Speaker,
    SpeakerAvailability,
    Submission,
    SubmissionSpeaker,
    Tag,
    Talk,
    User,
)

# Skip all tests in this file if no API token is provided
pytestmark = pytest.mark.skipif(
    not os.getenv('PRETALX_API_TOKEN'), reason='PRETALX_API_TOKEN environment variable not set'
)

# Use a public Pretalx instance for testing
TEST_EVENT_SLUG = os.getenv('PRETALX_TEST_EVENT', 'pyconde-pydata-berlin-2024')


@pytest.fixture(scope='module')
def client():
    """Create an authenticated PretalxClient for integration testing."""
    from pathlib import Path

    config = Config(
        cfg_path=Path.home() / '.pytanis' / 'config.toml', Pretalx=PretalxCfg(api_token=os.getenv('PRETALX_API_TOKEN'))
    )
    return PretalxClient(config=config)


@pytest.fixture(scope='module')
def event_slug():
    """Get the event slug to use for testing."""
    return TEST_EVENT_SLUG


class TestAllPretalxModels:
    """Test all Pretalx Pydantic models with live API data."""

    @pytest.mark.integration
    def test_me_model(self, client):
        """Test the Me model."""
        me = client.me()
        assert isinstance(me, Me)
        assert me.name is not None
        assert me.email is not None
        Me.model_validate(me.model_dump())

    @pytest.mark.integration
    def test_event_model(self, client, event_slug):
        """Test the Event model."""
        event = client.event(event_slug)
        assert isinstance(event, Event)
        assert event.slug == event_slug
        assert isinstance(event.name, MultiLingualStr)
        Event.model_validate(event.model_dump())

    @pytest.mark.integration
    def test_submission_models(self, client, event_slug):
        """Test Submission and related models."""
        _count, submissions = client.submissions(event_slug, params={'state': 'confirmed', 'limit': 2})

        for submission in submissions:
            assert isinstance(submission, Submission)

            # Test SubmissionSpeaker model
            for speaker in submission.speakers:
                assert isinstance(speaker, SubmissionSpeaker)

            # Test Answer model
            if submission.answers:
                for answer in submission.answers:
                    assert isinstance(answer, Answer)
                    assert isinstance(answer.question, AnswerQuestionRef)

            Submission.model_validate(submission.model_dump())

    @pytest.mark.integration
    def test_talk_models(self, client, event_slug):
        """Test Talk and related models."""
        _count, talks = client.talks(event_slug, params={'limit': 2})

        for talk in talks:
            assert isinstance(talk, Talk)

            # Test Slot model
            if talk.slot:
                assert isinstance(talk.slot, Slot)

            # Test Resource model
            if talk.resources:
                for resource in talk.resources:
                    assert isinstance(resource, Resource)

            Talk.model_validate(talk.model_dump())

    @pytest.mark.integration
    def test_speaker_models(self, client, event_slug):
        """Test Speaker and SpeakerAvailability models."""
        _count, speakers = client.speakers(event_slug, params={'limit': 2})

        for speaker in speakers:
            assert isinstance(speaker, Speaker)

            # Test SpeakerAvailability model
            if speaker.availabilities:
                for availability in speaker.availabilities:
                    assert isinstance(availability, SpeakerAvailability)

            Speaker.model_validate(speaker.model_dump())

    @pytest.mark.integration
    def test_room_models(self, client, event_slug):
        """Test Room and RoomAvailability models."""
        _count, rooms = client.rooms(event_slug)

        for room in rooms:
            assert isinstance(room, Room)
            assert isinstance(room.name, MultiLingualStr)

            # Test RoomAvailability model
            if room.availabilities:
                for availability in room.availabilities:
                    assert isinstance(availability, RoomAvailability)

            Room.model_validate(room.model_dump())

    @pytest.mark.integration
    def test_question_models(self, client, event_slug):
        """Test Question and Option models."""
        _count, questions = client.questions(event_slug)

        for question in questions:
            assert isinstance(question, Question)
            assert isinstance(question.question, MultiLingualStr)

            # Test Option model
            if question.options:
                for option in question.options:
                    assert isinstance(option, Option)

            Question.model_validate(question.model_dump())

    @pytest.mark.integration
    def test_tag_model(self, client, event_slug):
        """Test Tag model."""
        _count, tags = client.tags(event_slug)

        for tag in tags:
            assert isinstance(tag, Tag)
            Tag.model_validate(tag.model_dump())

    @pytest.mark.integration
    def test_review_models(self, client, event_slug):
        """Test Review and User models."""
        try:
            _count, reviews = client.reviews(event_slug, params={'limit': 2})

            for review in reviews:
                assert isinstance(review, Review)

                # Test User model
                if review.user:
                    assert isinstance(review.user, User)

                Review.model_validate(review.model_dump())
        except Exception as e:
            if '403' in str(e) or '401' in str(e):
                pytest.skip('No permission to access reviews')
            raise

    @pytest.mark.integration
    def test_answer_model(self, client, event_slug):
        """Test Answer model in detail."""
        _count, answers = client.answers(event_slug, params={'limit': 2})

        for answer in answers:
            assert isinstance(answer, Answer)
            assert isinstance(answer.question, AnswerQuestionRef)
            Answer.model_validate(answer.model_dump())


class TestModelRelationships:
    """Test relationships between models."""

    @pytest.mark.integration
    def test_submission_speaker_consistency(self, client, event_slug):
        """Test that submission speakers match speaker endpoint data."""
        _count, submissions = client.submissions(event_slug, params={'state': 'confirmed', 'limit': 1})

        submission = next(submissions, None)
        if submission and submission.speakers:
            for sub_speaker in submission.speakers:
                speaker = client.speaker(event_slug, sub_speaker.code)
                assert speaker.code == sub_speaker.code
                assert speaker.name == sub_speaker.name

    @pytest.mark.integration
    def test_slot_room_consistency(self, client, event_slug):
        """Test that talk slots reference valid rooms."""
        # Get rooms
        _count, rooms = client.rooms(event_slug)
        room_ids = {room.id for room in rooms}

        # Get talks with slots
        _count, talks = client.talks(event_slug, params={'limit': 5})

        for talk in talks:
            if talk.slot and talk.slot.room:
                # Room ID should exist
                assert talk.slot.room in room_ids

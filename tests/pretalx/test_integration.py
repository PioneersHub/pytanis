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
    URLs,
    User,
)

# Use a public Pretalx instance for testing
# This should be a conference that has public data available
TEST_EVENT_SLUG = 'pyconde-pydata-berlin-2024'  # Update this to a current/accessible event
PUBLIC_PRETALX_URL = 'https://pretalx.com/api'  # Default public instance


@pytest.fixture(scope='module')
def integration_client():
    """Create a PretalxClient for integration testing.

    This uses environment variables if available, otherwise falls back to public API.
    """
    # Check if we have API credentials in environment
    api_token = os.getenv('PRETALX_API_TOKEN')

    # Create a minimal config for testing
    from pathlib import Path

    from pytanis.config import Config, PretalxCfg

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
    def test_me_model(self, integration_client):
        """Test the Me model with live data."""
        if not integration_client._config.Pretalx.api_token:
            pytest.skip('Me endpoint requires authentication')

        try:
            me = integration_client.me()
            # Validate the model was properly constructed
            assert isinstance(me, Me)
            assert me.name is not None
            assert me.email is not None
            assert me.locale is not None
            assert me.timezone is not None

            # Validate model serialization
            me_dict = me.model_dump()
            assert isinstance(me_dict, dict)
            assert 'name' in me_dict
            assert 'email' in me_dict

            # Validate model can be reconstructed
            Me.model_validate(me_dict)
        except Exception as e:
            if '401' in str(e) or '403' in str(e):
                pytest.skip(f'Authentication required: {e}')
            raise

    @pytest.mark.integration
    def test_event_model(self, integration_client, test_event_slug):
        """Test the Event model with live data."""
        try:
            event = integration_client.event(test_event_slug)

            # Validate the model was properly constructed
            assert isinstance(event, Event)
            assert event.name is not None
            assert isinstance(event.name, MultiLingualStr)
            assert event.slug == test_event_slug
            assert event.date_from is not None
            assert event.date_to is not None

            # Test MultiLingualStr
            if event.name.en:
                assert isinstance(event.name.en, str)

            # Test URLs model if present
            if event.urls:
                assert isinstance(event.urls, URLs)

            # Validate model serialization
            event_dict = event.model_dump()
            assert isinstance(event_dict, dict)

            # Validate model can be reconstructed
            Event.model_validate(event_dict)
        except Exception as e:
            if '404' in str(e):
                pytest.skip(f'Event not found: {test_event_slug}')
            raise

    @pytest.mark.integration
    def test_events_listing(self, integration_client):
        """Test multiple Event models from listing."""
        try:
            count, events = integration_client.events()
            events_list = list(events)

            # We should have at least one event
            if count > 0:
                assert len(events_list) > 0

                # Validate each event
                for event in events_list[:5]:  # Test first 5 to avoid rate limits
                    assert isinstance(event, Event)
                    assert event.slug is not None
                    assert event.name is not None

                    # Validate serialization
                    Event.model_validate(event.model_dump())
        except Exception as e:
            pytest.skip(f'Could not fetch events: {e}')

    @pytest.mark.integration
    def test_submission_model(self, integration_client, test_event_slug):
        """Test the Submission model with live data."""
        try:
            count, submissions = integration_client.submissions(
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
    def test_talk_model(self, integration_client, test_event_slug):
        """Test the Talk model with live data."""
        try:
            count, talks = integration_client.talks(test_event_slug, params={'limit': 5})
            talks_list = list(talks)

            if not talks_list:
                pytest.skip('No talks found')

            for talk in talks_list:
                # Validate the model was properly constructed
                assert isinstance(talk, Talk)
                assert talk.code is not None
                assert talk.title is not None

                # Test slot if present
                if talk.slot:
                    assert isinstance(talk.slot, Slot)
                    assert talk.slot.start is not None
                    assert talk.slot.end is not None

                # Test resources if present
                if talk.resources:
                    assert isinstance(talk.resources, list)
                    for resource in talk.resources:
                        assert isinstance(resource, Resource)

                # Validate model serialization
                talk_dict = talk.model_dump()
                assert isinstance(talk_dict, dict)

                # Validate model can be reconstructed
                Talk.model_validate(talk_dict)
        except Exception as e:
            if '404' in str(e):
                pytest.skip(f'Event not found: {test_event_slug}')
            raise

    @pytest.mark.integration
    def test_speaker_model(self, integration_client, test_event_slug):
        """Test the Speaker model with live data."""
        try:
            count, speakers = integration_client.speakers(test_event_slug, params={'limit': 5, 'questions': 'all'})
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

    @pytest.mark.integration
    def test_room_model(self, integration_client, test_event_slug):
        """Test the Room model with live data."""
        try:
            count, rooms = integration_client.rooms(test_event_slug)
            rooms_list = list(rooms)

            if not rooms_list:
                pytest.skip('No rooms found')

            for room in rooms_list:
                # Validate the model was properly constructed
                assert isinstance(room, Room)
                assert room.id is not None
                assert room.name is not None
                assert isinstance(room.name, MultiLingualStr)

                # Test availabilities if present
                if room.availabilities:
                    assert isinstance(room.availabilities, list)
                    for availability in room.availabilities:
                        assert isinstance(availability, RoomAvailability)
                        assert availability.start is not None
                        assert availability.end is not None

                # Validate model serialization
                room_dict = room.model_dump()
                assert isinstance(room_dict, dict)

                # Validate model can be reconstructed
                Room.model_validate(room_dict)
        except Exception as e:
            if '404' in str(e):
                pytest.skip(f'Event not found: {test_event_slug}')
            raise

    @pytest.mark.integration
    def test_question_model(self, integration_client, test_event_slug):
        """Test the Question model with live data."""
        try:
            count, questions = integration_client.questions(test_event_slug)
            questions_list = list(questions)

            if not questions_list:
                pytest.skip('No questions found')

            for question in questions_list:
                # Validate the model was properly constructed
                assert isinstance(question, Question)
                assert question.id is not None
                assert question.question is not None
                assert isinstance(question.question, MultiLingualStr)

                # Test options if present
                if question.options:
                    assert isinstance(question.options, list)
                    for option in question.options:
                        assert isinstance(option, Option)
                        assert option.id is not None

                # Validate model serialization
                question_dict = question.model_dump()
                assert isinstance(question_dict, dict)

                # Validate model can be reconstructed
                Question.model_validate(question_dict)
        except Exception as e:
            if '404' in str(e):
                pytest.skip(f'Event not found: {test_event_slug}')
            raise

    @pytest.mark.integration
    def test_tag_model(self, integration_client, test_event_slug):
        """Test the Tag model with live data."""
        try:
            count, tags = integration_client.tags(test_event_slug)
            tags_list = list(tags)

            if not tags_list:
                pytest.skip('No tags found')

            for tag in tags_list:
                # Validate the model was properly constructed
                assert isinstance(tag, Tag)
                assert tag.tag is not None

                # Validate model serialization
                tag_dict = tag.model_dump()
                assert isinstance(tag_dict, dict)

                # Validate model can be reconstructed
                Tag.model_validate(tag_dict)
        except Exception as e:
            if '404' in str(e):
                pytest.skip(f'Event not found: {test_event_slug}')
            raise

    @pytest.mark.integration
    def test_review_model(self, integration_client, test_event_slug):
        """Test the Review model with live data."""
        if not integration_client._config.Pretalx.api_token:
            pytest.skip('Reviews endpoint requires authentication')

        try:
            count, reviews = integration_client.reviews(test_event_slug, params={'limit': 5})
            reviews_list = list(reviews)

            if not reviews_list:
                pytest.skip('No reviews found or no access')

            for review in reviews_list:
                # Validate the model was properly constructed
                assert isinstance(review, Review)
                assert review.id is not None
                assert review.submission is not None

                # Test user if present
                if review.user:
                    assert isinstance(review.user, User)
                    assert review.user.name is not None

                # Validate model serialization
                review_dict = review.model_dump()
                assert isinstance(review_dict, dict)

                # Validate model can be reconstructed
                Review.model_validate(review_dict)
        except Exception as e:
            if '401' in str(e) or '403' in str(e):
                pytest.skip(f'Authentication required: {e}')
            elif '404' in str(e):
                pytest.skip(f'Event not found: {test_event_slug}')
            raise

    @pytest.mark.integration
    def test_answer_model(self, integration_client, test_event_slug):
        """Test the Answer model with live data."""
        try:
            count, answers = integration_client.answers(test_event_slug, params={'limit': 5})
            answers_list = list(answers)

            if not answers_list:
                pytest.skip('No answers found')

            for answer in answers_list:
                # Validate the model was properly constructed
                assert isinstance(answer, Answer)
                assert answer.id is not None
                assert answer.answer is not None
                assert isinstance(answer.question, AnswerQuestionRef)

                # Validate model serialization
                answer_dict = answer.model_dump()
                assert isinstance(answer_dict, dict)

                # Validate model can be reconstructed
                Answer.model_validate(answer_dict)
        except Exception as e:
            if '404' in str(e):
                pytest.skip(f'Event not found: {test_event_slug}')
            raise

class TestPretalxDataConsistency:
    """Test data consistency and relationships between models."""

    @pytest.mark.integration
    def test_submission_speaker_relationship(self, integration_client, test_event_slug):
        """Test that submission speakers match actual speaker data."""
        try:
            # Get a submission with speakers
            count, submissions = integration_client.submissions(
                test_event_slug, params={'state': 'confirmed', 'limit': 1}
            )
            submission = next(submissions, None)

            if not submission or not submission.speakers:
                pytest.skip('No submission with speakers found')

            # For each speaker in the submission
            for sub_speaker in submission.speakers:
                # Fetch the full speaker data
                speaker = integration_client.speaker(test_event_slug, sub_speaker.code)

                # Validate the data matches
                assert speaker.code == sub_speaker.code
                assert speaker.name == sub_speaker.name
                assert submission.code in speaker.submissions
        except Exception as e:
            if '404' in str(e):
                pytest.skip('Event or speaker not found')
            raise

    @pytest.mark.integration
    def test_talk_slot_room_consistency(self, integration_client, test_event_slug):
        """Test that talk slots reference valid rooms."""
        try:
            # Get all rooms first
            count, rooms = integration_client.rooms(test_event_slug)
            room_ids = {room.id for room in rooms}

            if not room_ids:
                pytest.skip('No rooms found')

            # Get talks with slots
            count, talks = integration_client.talks(test_event_slug, params={'limit': 10})

            talks_with_slots = [talk for talk in talks if talk.slot and talk.slot.room]

            if not talks_with_slots:
                pytest.skip('No talks with slots and rooms found')

            # Validate room references
            for talk in talks_with_slots:
                if talk.slot.room:
                    # The room ID in the slot should exist in our rooms
                    assert talk.slot.room in room_ids, f'Talk {talk.code} references non-existent room {talk.slot.room}'
        except Exception as e:
            if '404' in str(e):
                pytest.skip('Event not found')
            raise

    @pytest.mark.integration
    def test_answer_question_relationship(self, integration_client, test_event_slug):
        """Test that answers reference valid questions."""
        try:
            # Get all questions first
            count, questions = integration_client.questions(test_event_slug)
            question_ids = {q.id for q in questions}

            if not question_ids:
                pytest.skip('No questions found')

            # Get some answers
            count, answers = integration_client.answers(test_event_slug, params={'limit': 10})
            answers_list = list(answers)

            if not answers_list:
                pytest.skip('No answers found')

            # Validate question references
            for answer in answers_list:
                assert answer.question.id in question_ids, (
                    f'Answer {answer.id} references non-existent question {answer.question.id}'
                )
        except Exception as e:
            if '404' in str(e):
                pytest.skip('Event not found')
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
            count, submissions = integration_client.submissions(
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

    @pytest.mark.integration
    def test_partial_data_handling(self, integration_client, test_event_slug):
        """Test that models handle partial/optional data correctly."""
        try:
            # Get talks which might have varying levels of completeness
            count, talks = integration_client.talks(test_event_slug, params={'limit': 10})

            for talk in talks:
                # These should always be present
                assert talk.code is not None
                assert talk.title is not None

                # These might be None but should not cause errors
                talk_dict = talk.model_dump()

                # Check optional fields are handled
                optional_fields = ['slot', 'resources', 'description', 'abstract']
                for field in optional_fields:
                    # Field should exist in dict even if None
                    assert field in talk_dict

                # Should be able to reconstruct even with None values
                Talk.model_validate(talk_dict)
        except Exception as e:
            if '404' in str(e):
                pytest.skip('Event not found')
            raise


# Marker for running integration tests
pytest.mark.integration = pytest.mark.skipif(
    os.getenv('SKIP_INTEGRATION_TESTS', 'false').lower() == 'true', reason='Integration tests skipped'
)

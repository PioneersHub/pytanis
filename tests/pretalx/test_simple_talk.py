"""Tests for the SimpleTalk functionality"""

import json
from unittest.mock import MagicMock

from pytanis.pretalx.models import (
    Answer,
    AnswerQuestionRef,
    MultiLingualStr,
    SimpleTalk,
    Speaker,
    State,
    SubmissionSpeaker,
    Talk,
)
from pytanis.pretalx.utils import talks_to_json


def test_simple_talk_model():
    """Test that the SimpleTalk model works as expected"""
    talk = SimpleTalk(
        title='Test Talk',
        speaker='John Doe, Jane Smith',
        organisation='Acme Inc.',
        track='Python',
        domain_level='Intermediate',
        python_level='Advanced',
        duration='45',
        abstract='This is an abstract',
        description='This is a description',
        prerequisites='Python basics',
    )

    assert talk.title == 'Test Talk'
    assert talk.speaker == 'John Doe, Jane Smith'
    assert talk.organisation == 'Acme Inc.'
    assert talk.track == 'Python'
    assert talk.domain_level == 'Intermediate'
    assert talk.python_level == 'Advanced'
    assert talk.duration == '45'
    assert talk.abstract == 'This is an abstract'
    assert talk.description == 'This is a description'
    assert talk.prerequisites == 'Python basics'


def test_talks_to_json():
    """Test that talks_to_json works as expected"""
    # Create mock Talk objects
    talk1 = Talk(
        code='ABC123',
        title='Python Best Practices',
        speakers=[
            SubmissionSpeaker(code='S1', name='John Doe'),
            SubmissionSpeaker(code='S2', name='Jane Smith'),
        ],
        submission_type=MultiLingualStr(en='Talk'),
        submission_type_id=1,
        track=MultiLingualStr(en='Python'),
        state=State.confirmed,
        abstract='Abstract for talk 1',
        description='Description for talk 1',
        duration=45,
        do_not_record=False,
        is_featured=False,
        content_locale='en',
        slot_count=1,
        resources=[],
        answers=[
            Answer(
                id=1,
                answer='Intermediate',
                question=AnswerQuestionRef(id=1, question=MultiLingualStr(en='Expected audience expertise: Domain')),
                options=[],
            ),
            Answer(
                id=2,
                answer='Advanced',
                question=AnswerQuestionRef(id=2, question=MultiLingualStr(en='Expected audience expertise: Python')),
                options=[],
            ),
            Answer(
                id=3,
                answer='Python 3.6+',
                question=AnswerQuestionRef(id=3, question=MultiLingualStr(en='Prerequisites')),
                options=[],
            ),
        ],
    )

    # Create mock speaker objects with Company / Institute information
    speaker1 = Speaker(
        code='S1',
        name='John Doe',
        submissions=['ABC123'],
        answers=[
            Answer(
                id=10,
                answer='Acme Inc.',
                question=AnswerQuestionRef(id=10, question=MultiLingualStr(en='Company / Institute')),
                person='S1',
                options=[],
            ),
        ],
    )

    speaker2 = Speaker(
        code='S2',
        name='Jane Smith',
        submissions=['ABC123'],
        answers=[
            Answer(
                id=11,
                answer='Acme Inc.',
                question=AnswerQuestionRef(id=11, question=MultiLingualStr(en='Company / Institute')),
                person='S2',
                options=[],
            ),
        ],
    )

    talk2 = Talk(
        code='DEF456',
        title='Introduction to Django',
        speakers=[SubmissionSpeaker(code='S3', name='Bob Johnson')],
        submission_type=MultiLingualStr(en='Talk'),
        submission_type_id=1,
        track=MultiLingualStr(en='Web'),
        state=State.confirmed,
        abstract='Abstract for talk 2',
        description='Description for talk 2',
        duration=30,
        do_not_record=False,
        is_featured=False,
        content_locale='en',
        slot_count=1,
        resources=[],
        answers=[],
    )

    # Create speaker with Company / Institute information
    speaker3 = Speaker(
        code='S3',
        name='Bob Johnson',
        submissions=['DEF456'],
        answers=[
            Answer(
                id=12,
                answer='Django Corp',
                question=AnswerQuestionRef(id=12, question=MultiLingualStr(en='Company / Institute')),
                person='S3',
                options=[],
            ),
        ],
    )

    # Create a talk that is not confirmed (should be filtered out)
    talk3 = Talk(
        code='GHI789',
        title='Rejected Talk',
        speakers=[SubmissionSpeaker(code='S4', name='Alice Brown')],
        submission_type=MultiLingualStr(en='Talk'),
        submission_type_id=1,
        track=None,
        state=State.rejected,
        abstract='Abstract',
        description='Description',
        duration=None,
        do_not_record=False,
        is_featured=False,
        content_locale='en',
        slot_count=1,
        resources=[],
        answers=[],
    )

    # Set up the mock pretalx client
    mock_client = MagicMock()
    mock_client.speaker.side_effect = lambda event_slug, code, params: {
        'S1': speaker1,
        'S2': speaker2,
        'S3': speaker3,
    }[code]

    # Get JSON with the mock client - only pass confirmed talks
    json_str = talks_to_json([talk1, talk2], mock_client, 'test-event')

    # Parse JSON
    talks = json.loads(json_str)

    # Check that we have the right number of talks
    assert len(talks) == 2

    # Check the first talk
    assert talks[0]['title'] == 'Python Best Practices'
    assert talks[0]['speaker'] == 'John Doe, Jane Smith'
    assert talks[0]['organisation'] == 'Acme Inc.'
    assert talks[0]['track'] == 'Python'
    assert talks[0]['domain_level'] == 'Intermediate'
    assert talks[0]['python_level'] == 'Advanced'
    assert talks[0]['duration'] == '45'
    assert talks[0]['abstract'] == 'Abstract for talk 1'
    assert talks[0]['description'] == 'Description for talk 1'
    assert talks[0]['prerequisites'] == 'Python 3.6+'

    # Check the second talk
    assert talks[1]['title'] == 'Introduction to Django'
    assert talks[1]['speaker'] == 'Bob Johnson'
    assert talks[1]['organisation'] == 'Django Corp'
    assert talks[1]['track'] == 'Web'
    assert talks[1]['domain_level'] == ''  # No domain level info
    assert talks[1]['python_level'] == ''  # No python level info
    assert talks[1]['duration'] == '30'
    assert talks[1]['abstract'] == 'Abstract for talk 2'
    assert talks[1]['description'] == 'Description for talk 2'
    assert talks[1]['prerequisites'] == ''  # No prerequisites info

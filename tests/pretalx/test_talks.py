"""Tests for the talk utilities"""

import json
from unittest.mock import MagicMock, patch

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
from pytanis.pretalx.utils import (
    create_simple_talk_from_talk,
    extract_expertise_and_prerequisites,
    extract_organisation,
    find_answer_by_pattern,
    get_talks_as_json,
    save_talks_to_json,
    talks_to_json,
)


def test_find_answer_by_pattern():
    """Test finding answers by pattern or keywords"""
    # Create test answers
    answers = [
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
            question=AnswerQuestionRef(id=3, question=MultiLingualStr(en='Prerequisites for this talk')),
            options=[],
        ),
    ]

    # Test exact pattern matching (case sensitive)
    result = find_answer_by_pattern(answers, 'Expected audience expertise: Domain')
    assert result == 'Intermediate'

    # Test exact pattern matching (case insensitive)
    result = find_answer_by_pattern(answers, 'expected audience expertise: python', case_sensitive=False)
    assert result == 'Advanced'

    # Test keyword matching
    result = find_answer_by_pattern(answers, '', case_sensitive=False, keywords=['prerequisite'])
    assert result == 'Python 3.6+'

    # Test multiple keywords
    result = find_answer_by_pattern(answers, '', case_sensitive=False, keywords=['requirement', 'prerequisite'])
    assert result == 'Python 3.6+'

    # Test no match
    result = find_answer_by_pattern(answers, 'Not Found')
    assert result == ''

    # Test empty answers list
    result = find_answer_by_pattern([], 'Any Pattern')
    assert result == ''


def test_create_simple_talk_from_talk():
    """Test creating a SimpleTalk from a Talk"""
    talk = Talk(
        code='ABC123',
        title='Test Talk',
        speakers=[
            SubmissionSpeaker(code='S1', name='John Doe'),
            SubmissionSpeaker(code='S2', name='Jane Smith'),
        ],
        submission_type=MultiLingualStr(en='Talk'),
        submission_type_id=1,
        track=MultiLingualStr(en='Python'),
        state=State.confirmed,
        abstract='Test abstract',
        description='Test description',
        duration=45,
        do_not_record=False,
        is_featured=False,
        content_locale='en',
        slot_count=1,
        resources=[],
        answers=[],
    )

    simple_talk = create_simple_talk_from_talk(talk)

    assert simple_talk.code == 'ABC123'
    assert simple_talk.title == 'Test Talk'
    assert simple_talk.speaker == 'John Doe, Jane Smith'
    assert simple_talk.track == 'Python'
    assert simple_talk.duration == '45'
    assert simple_talk.abstract == 'Test abstract'
    assert simple_talk.description == 'Test description'


def test_extract_expertise_and_prerequisites():
    """Test extracting expertise and prerequisites"""
    talk = Talk(
        code='ABC123',
        title='Test Talk',
        speakers=[SubmissionSpeaker(code='S1', name='John Doe')],
        submission_type=MultiLingualStr(en='Talk'),
        submission_type_id=1,
        track=MultiLingualStr(en='Python'),
        state=State.confirmed,
        abstract='Test abstract',
        description='Test description',
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

    simple_talk = SimpleTalk(title=talk.title)
    extract_expertise_and_prerequisites(talk, simple_talk)

    assert simple_talk.domain_level == 'Intermediate'
    assert simple_talk.python_level == 'Advanced'
    assert simple_talk.prerequisites == 'Python 3.6+'


def test_extract_organisation():
    """Test extracting organisation information"""
    talk = Talk(
        code='ABC123',
        title='Test Talk',
        speakers=[
            SubmissionSpeaker(code='S1', name='John Doe'),
            SubmissionSpeaker(code='S2', name='Jane Smith'),
        ],
        submission_type=MultiLingualStr(en='Talk'),
        submission_type_id=1,
        track=MultiLingualStr(en='Python'),
        state=State.confirmed,
        abstract='Test abstract',
        description='Test description',
        duration=45,
        do_not_record=False,
        is_featured=False,
        content_locale='en',
        slot_count=1,
        resources=[],
        answers=[],
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

    # Set up the mock pretalx client
    mock_client = MagicMock()
    mock_client.speaker.side_effect = lambda event_slug, code, params: {
        'S1': speaker1,
        'S2': speaker2,
    }[code]

    simple_talk = SimpleTalk(title=talk.title)
    speaker_data = {}

    extract_organisation(talk, simple_talk, mock_client, 'test-event', speaker_data)

    assert simple_talk.organisation == 'Acme Inc.'
    assert len(speaker_data) == 2
    assert speaker_data['S1'] == speaker1
    assert speaker_data['S2'] == speaker2


@patch('pytanis.pretalx.utils.talks_to_json')
def test_get_talks_as_json(mock_talks_to_json):
    """Test get_talks_as_json function"""
    # Set up mock
    mock_talks_to_json.return_value = '[]'

    # Set up mock pretalx client
    mock_client = MagicMock()
    mock_client.talks.return_value = (0, [])

    # Call function
    result = get_talks_as_json(mock_client, 'test-event', 'accepted')

    # Check results
    assert result == '[]'
    mock_client.talks.assert_called_once_with('test-event', params={'questions': 'all', 'state': 'accepted'})
    mock_talks_to_json.assert_called_once()


@patch('builtins.open', new_callable=MagicMock)
@patch('pytanis.pretalx.utils.get_talks_as_json')
def test_save_talks_to_json(mock_get_talks_as_json, mock_open):
    """Test save_talks_to_json function"""
    # Set up mock
    mock_get_talks_as_json.return_value = '[]'
    mock_client = MagicMock()

    # Call function
    save_talks_to_json(mock_client, 'test-event', 'test.json', 'accepted')

    # Check results
    mock_get_talks_as_json.assert_called_once_with(mock_client, 'test-event', 'accepted', None)
    mock_open.assert_called_once_with('test.json', 'w', encoding='utf-8')
    mock_open.return_value.__enter__.return_value.write.assert_called_once_with('[]')


def test_talks_to_json():
    """Test talks_to_json function"""
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

    # Set up the mock pretalx client
    mock_client = MagicMock()
    mock_client.speaker.side_effect = lambda event_slug, code, params: {
        'S1': speaker1,
        'S2': speaker2,
    }[code]

    # Get JSON with the mock client
    json_str = talks_to_json([talk1], mock_client, 'test-event')

    # Parse JSON
    talks = json.loads(json_str)

    # Check that we have the right number of talks
    assert len(talks) == 1

    # Check the talk
    assert talks[0]['code'] == 'ABC123'
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

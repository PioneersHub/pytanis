"""Test backward compatibility with new API changes"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from pytanis.pretalx import PretalxClient
from pytanis.pretalx.models import MultiLingualStr, SubmissionSpeaker


@pytest.fixture
def mock_responses():
    """Mock API responses for testing"""
    return {
        'submission': {
            'code': 'TEST123',
            'title': 'Test Talk',
            'speakers': ['SPEAKER1', 'SPEAKER2'],  # New format: speaker codes
            'submission_type': 5091,  # New format: type ID
            'track': 5205,  # New format: track ID
            'state': 'confirmed',
            'abstract': 'Test abstract',
            'description': 'Test description',
            'duration': 30,
            'slot_count': 1,
            'content_locale': 'en',
            'do_not_record': False,
            'resources': [123, 456],  # New format: resource IDs
            'slots': [],
            'answers': [789, 790],  # New format: answer IDs
            'pending_state': None,
            'notes': '',
            'internal_notes': None,
            # New fields not in old model
            'reviews': [1, 2, 3],
            'median_score': 4.5,
            'is_anonymised': False,
        },
        'speaker1': {
            'code': 'SPEAKER1',
            'name': 'John Doe',
            'biography': 'Bio 1',
            'submissions': ['TEST123'],
            'answers': [100, 101],  # New format
            # New fields
            'email': 'john@example.com',
            'timezone': 'UTC',
        },
        'speaker2': {
            'code': 'SPEAKER2',
            'name': 'Jane Smith',
            'biography': 'Bio 2',
            'submissions': ['TEST123'],
            'answers': [],
        },
        'submission_type': {
            'id': 5091,
            'name': {'en': 'Talk', 'de': 'Vortrag'},
            'default_duration': 30,
        },
        'track': {
            'id': 5205,
            'name': {'en': 'Python', 'de': 'Python'},
            'color': '#FF0000',
        },
    }


@patch.object(PretalxClient, '_get_one')
def test_submission_expansion(mock_get_one, mock_responses):
    """Test that submissions are properly expanded for backward compatibility"""
    client = PretalxClient()

    # Mock the API calls
    def get_one_side_effect(endpoint, params=None):
        if '/submissions/' in endpoint and endpoint.endswith('/'):
            return mock_responses['submission']
        elif '/speakers/SPEAKER1/' in endpoint:
            return mock_responses['speaker1']
        elif '/speakers/SPEAKER2/' in endpoint:
            return mock_responses['speaker2']
        elif '/submission-types/5091/' in endpoint:
            return mock_responses['submission_type']
        elif '/tracks/5205/' in endpoint:
            return mock_responses['track']
        elif '/answers/' in endpoint:
            return None  # Simulate no access to answers
        else:
            msg = f'Unexpected endpoint: {endpoint}'
            raise ValueError(msg)

    mock_get_one.side_effect = get_one_side_effect

    # Test single submission
    submission = client.submission('test-event', 'TEST123')

    # Check speaker expansion
    assert hasattr(submission, 'speakers')
    assert len(submission.speakers) == 2
    assert isinstance(submission.speakers[0], SubmissionSpeaker)
    assert submission.speakers[0].code == 'SPEAKER1'
    assert submission.speakers[0].name == 'John Doe'
    assert submission.speakers[1].code == 'SPEAKER2'
    assert submission.speakers[1].name == 'Jane Smith'

    # Check submission type expansion
    assert isinstance(submission.submission_type, MultiLingualStr)
    assert submission.submission_type.en == 'Talk'
    assert submission.submission_type.de == 'Vortrag'
    assert hasattr(submission, 'submission_type_id')
    assert submission.submission_type_id == 5091

    # Check track expansion
    assert isinstance(submission.track, MultiLingualStr)
    assert submission.track.en == 'Python'

    # Check that new fields are removed
    assert not hasattr(submission, 'reviews')
    assert not hasattr(submission, 'median_score')
    assert not hasattr(submission, 'is_anonymised')

    # Check that is_featured is added with default
    assert hasattr(submission, 'is_featured')
    assert submission.is_featured is False

    # Check that resources are cleared (as we can't expand them)
    assert submission.resources == []


@patch.object(PretalxClient, '_get_many')
@patch.object(PretalxClient, '_get_one')
def test_talks_fallback(mock_get_one, mock_get_many, mock_responses):
    """Test that talks endpoint falls back to submissions when 404"""
    client = PretalxClient()

    # First call to talks endpoint returns 404
    mock_response_404 = MagicMock()
    mock_response_404.status_code = 404
    mock_get_many.side_effect = httpx.HTTPStatusError(
        'Not found',
        request=MagicMock(),
        response=mock_response_404
    )

    # Mock speaker/type/track lookups
    def get_one_side_effect(endpoint, params=None):
        if '/speakers/SPEAKER1/' in endpoint:
            return mock_responses['speaker1']
        elif '/speakers/SPEAKER2/' in endpoint:
            return mock_responses['speaker2']
        elif '/submission-types/5091/' in endpoint:
            return mock_responses['submission_type']
        elif '/tracks/5205/' in endpoint:
            return mock_responses['track']
        else:
            return None

    mock_get_one.side_effect = get_one_side_effect

    # Override to return submissions on second call
    def get_many_side_effect(endpoint, params=None):
        if '/talks/' in endpoint:
            raise httpx.HTTPStatusError('Not found', request=MagicMock(), response=mock_response_404)
        elif '/submissions/' in endpoint:
            return 1, iter([mock_responses['submission']])
        else:
            msg = f'Unexpected endpoint: {endpoint}'
            raise ValueError(msg)

    mock_get_many.side_effect = get_many_side_effect

    # Call talks - should fallback to submissions
    count, talks = client.talks('test-event')
    talks_list = list(talks)

    assert len(talks_list) == 1
    talk = talks_list[0]

    # Should be validated as Talk but with submission data
    assert talk.code == 'TEST123'
    assert talk.title == 'Test Talk'
    assert len(talk.speakers) == 2
    assert isinstance(talk.speakers[0], SubmissionSpeaker)

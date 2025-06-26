"""Utilities related to Pretalx"""

import json
import logging
from collections.abc import Iterable
from typing import Any

import pandas as pd

from pytanis.pretalx.client import PretalxClient
from pytanis.pretalx.models import Answer, Review, SimpleTalk, Speaker, Submission, Talk

_logger = logging.getLogger(__name__)


class Col:
    """Convention of Pretalx column names for the functions below."""

    submission = 'Submission'
    submission_type = 'Submission type'
    submission_type_id = 'Submission type id'
    title = 'Title'
    duration = 'Duration'
    public = 'Public'
    track = 'Track'
    comment = 'Comment'
    created = 'Created'
    state = 'State'
    pending_state = 'Pending state'

    speaker_name = 'Speaker name'
    speaker_code = 'Speaker code'
    pretalx_user = 'Pretalx user'
    biography = 'Biography'
    affiliation = 'Affiliation'
    email = 'Email'
    availability = 'Availability'
    availability_comment = 'Availability Comment'

    nreviews = '#Reviews'
    review_score = 'Review Score'


def subs_as_df(
    subs: Iterable[Submission], *, with_questions: bool = False, question_prefix: str = 'Q: '
) -> pd.DataFrame:
    """Convert submissions into a dataframe

    Make sure to have `params={"questions": "all"}` for the PretalxAPI if `with_questions` is True.
    """
    rows = []
    for sub in subs:
        row = {
            Col.submission: sub.code,
            Col.title: sub.title,
            Col.track: sub.track.en if sub.track else None,
            Col.speaker_code: [speaker.code for speaker in sub.speakers],
            Col.speaker_name: [speaker.name for speaker in sub.speakers],
            Col.duration: sub.duration,
            Col.submission_type: (
                sub.submission_type.en if hasattr(sub.submission_type, 'en') else str(sub.submission_type)
            ),
            Col.submission_type_id: sub.submission_type_id,
            Col.state: sub.state.value,
            Col.pending_state: None if sub.pending_state is None else sub.pending_state.value,
            Col.created: sub.created,
        }
        if with_questions and sub.answers is not None:
            for answer in sub.answers:
                row[f'{question_prefix}{answer.question.question.en}'] = answer.answer
        rows.append(row)
    return pd.DataFrame(rows)


def speakers_as_df(
    speakers: Iterable[Speaker], *, with_questions: bool = False, question_prefix: str = 'Q: '
) -> pd.DataFrame:
    """Convert speakers into a dataframe

    Make sure to have `params={"questions": "all"}` for the PretalxAPI if `with_questions` is True.
    """
    rows = []
    for speaker in speakers:
        row = {
            Col.speaker_code: speaker.code,
            Col.speaker_name: speaker.name,
            Col.email: speaker.email,
            Col.biography: speaker.biography,
            Col.submission: speaker.submissions,
        }
        if with_questions and speaker.answers is not None:
            for answer in speaker.answers:
                # The API returns also questions that are 'per proposal/submission', we get these using the
                # submission endpoint and don't want them here due to ambiguity if several submission were made.
                if answer.person is not None:
                    row[f'{question_prefix}{answer.question.question.en}'] = answer.answer
        rows.append(row)
    return pd.DataFrame(rows)


def reviews_as_df(reviews: Iterable[Review]) -> pd.DataFrame:
    """Convert the reviews to a dataframe"""
    df = pd.DataFrame([review.model_dump() for review in reviews])
    # make first letter of column upper-case in accordance with our convention
    df.rename(columns={col: col.title() for col in df.columns}, inplace=True)
    # user is the speaker name to use for joining
    df.rename(columns={'User': Col.pretalx_user, 'Score': Col.review_score}, inplace=True)

    return df


def create_simple_talk_from_talk(talk: Talk) -> SimpleTalk:
    """Create a SimpleTalk object with basic information from a Talk object."""
    track_value = ''
    if talk.track is not None and talk.track.en is not None:
        track_value = talk.track.en

    return SimpleTalk(
        code=talk.code,
        title=talk.title,
        speaker=', '.join([speaker.name for speaker in talk.speakers]),
        track=track_value,
        duration=str(talk.duration) if talk.duration else '',
        abstract=talk.abstract,
        description=talk.description,
    )


def find_answer_by_pattern(
    answers: list[Answer], pattern: str, *, case_sensitive: bool = True, keywords: list[str] | None = None
) -> str:
    """Find an answer by matching a pattern or keywords in the question text.

    Args:
        answers: List of Answer objects to search through
        pattern: Exact pattern to search for in question text
        case_sensitive: Whether the pattern matching should be case sensitive
        keywords: List of keywords to search for in question text (case insensitive)

    Returns:
        The answer text if found, empty string otherwise
    """
    if not answers:
        return ''

    for answer in answers:
        question_text = answer.question.question.en or ''

        # Check for exact pattern match
        if pattern:
            if case_sensitive and pattern in question_text:
                return answer.answer
            elif not case_sensitive and pattern.lower() in question_text.lower():
                return answer.answer

        # Check for keywords match
        if keywords and any(keyword.lower() in question_text.lower() for keyword in keywords):
            return answer.answer

    return ''


def extract_expertise_and_prerequisites(talk: Talk, simple_talk: SimpleTalk) -> None:
    """Extract expertise levels and prerequisites from talk answers."""
    if not talk.answers:
        return

    # Extract domain expertise level
    domain_expertise = find_answer_by_pattern(talk.answers, 'Expected audience expertise: Domain')

    # Extract Python expertise level
    python_expertise = find_answer_by_pattern(talk.answers, 'Expected audience expertise: Python')

    # Extract prerequisites using keywords
    prerequisites = find_answer_by_pattern(
        talk.answers, '', case_sensitive=False, keywords=['prerequisite', 'requirement', 'needed', 'necessary']
    )

    # Set the extracted values
    simple_talk.domain_level = domain_expertise
    simple_talk.python_level = python_expertise
    simple_talk.prerequisites = prerequisites


def extract_organisation(
    talk: Talk,
    simple_talk: SimpleTalk,
    pretalx_client: PretalxClient,
    event_slug: str,
    speaker_data: dict[str, Speaker],
) -> None:
    """Extract organisation information from speaker data."""
    if not (pretalx_client and event_slug):
        return

    organisations = []

    for speaker in talk.speakers:
        # Check if we already have this speaker's data
        if speaker.code not in speaker_data:
            try:
                # Fetch speaker data with answers
                speaker_data[speaker.code] = pretalx_client.speaker(
                    event_slug, speaker.code, params={'questions': 'all'}
                )
            except Exception as e:
                # If there's an error fetching speaker data, just continue
                _logger.error(f'Error fetching data for speaker {speaker.code}: {e}')
                continue

        # Get the speaker with full data including answers
        full_speaker = speaker_data[speaker.code]

        # Look for "Company / Institute" in speaker answers
        if full_speaker.answers:
            # Filter to only include speaker-specific answers
            speaker_answers = [answer for answer in full_speaker.answers if answer.person is not None]

            # Find the organisation using our helper function
            organisation = find_answer_by_pattern(speaker_answers, 'Company / Institute')
            if organisation.strip():
                organisations.append(organisation.strip())

    # If we found organisations in the speaker answers, use them
    if organisations:
        # Remove duplicates while preserving order
        unique_organisations = []
        for org in organisations:
            if org not in unique_organisations:
                unique_organisations.append(org)
        simple_talk.organisation = ', '.join(unique_organisations)


def get_talks_as_json(
    pretalx_client: PretalxClient, event_slug: str, state_value: str = 'confirmed', params: dict[str, Any] | None = None
) -> str:
    """
    Get talks from pretalx and convert them to a JSON list of SimpleTalk objects.

    This function fetches talks from pretalx based on the specified state,
    extracts the essential information, and returns a JSON string containing
    a list of simplified talk objects.

    Args:
        pretalx_client: PretalxClient instance to fetch talk and speaker data
        event_slug: Event slug for the pretalx event
        state_value: State of talks to include (default: "confirmed")
        params: Additional parameters to pass to the pretalx API

    Returns:
        A JSON string containing a list of SimpleTalk objects
    """
    # Prepare parameters for the API call
    if params is None:
        params = {}

    # Ensure we get all questions and filter by state
    params['questions'] = 'all'
    params['state'] = state_value

    # Fetch talks from pretalx
    _, talks_iter = pretalx_client.talks(event_slug, params=params)
    talks = list(talks_iter)  # Materialize the iterator

    return talks_to_json(talks, pretalx_client, event_slug)


def talks_to_json(
    talks: Iterable[Talk], pretalx_client: PretalxClient | None = None, event_slug: str | None = None
) -> str:
    """
    Convert Talk objects to a JSON list of SimpleTalk objects.

    This function extracts the essential information from pretalx Talk objects
    and returns a JSON string containing a list of simplified talk objects.

    Args:
        talks: An iterable of Talk objects
        pretalx_client: Optional PretalxClient instance to fetch speaker data
        event_slug: Optional event slug needed if pretalx_client is provided

    Returns:
        A JSON string containing a list of SimpleTalk objects
    """
    simple_talks = []

    # Store speaker data to avoid fetching the same speaker multiple times
    speaker_data: dict[str, Speaker] = {}

    for talk in talks:
        # Create a SimpleTalk object with basic information
        simple_talk = create_simple_talk_from_talk(talk)

        # Extract expertise levels and prerequisites
        extract_expertise_and_prerequisites(talk, simple_talk)

        # Extract organisation information
        if event_slug and pretalx_client:
            extract_organisation(talk, simple_talk, pretalx_client, event_slug, speaker_data)

        simple_talks.append(simple_talk)

    # Convert to JSON
    return json.dumps([talk.model_dump() for talk in simple_talks], indent=2)


def save_talks_to_json(
    pretalx_client: PretalxClient,
    event_slug: str,
    file_path: str,
    state_value: str = 'confirmed',
    params: dict[str, Any] | None = None,
) -> None:
    """
    Fetch talks from pretalx and save them to a JSON file.

    Args:
        pretalx_client: PretalxClient instance to fetch talk and speaker data
        event_slug: Event slug for the pretalx event
        file_path: Path where the JSON file should be saved
        state_value: State of talks to include (default: "confirmed")
        params: Additional parameters to pass to the pretalx API
    """
    json_data = get_talks_as_json(pretalx_client, event_slug, state_value, params)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json_data)


def save_confirmed_talks_to_json(
    talks: Iterable[Talk], file_path: str, pretalx_client: PretalxClient | None = None, event_slug: str | None = None
) -> None:
    """
    Save confirmed talks to a JSON file (legacy function for backward compatibility).

    Args:
        talks: An iterable of Talk objects, typically from pretalx_client.talks()
        file_path: Path where the JSON file should be saved
        pretalx_client: Optional PretalxClient instance to fetch speaker data
        event_slug: Optional event slug needed if pretalx_client is provided
    """
    json_data = talks_to_json([talk for talk in talks if talk.state.value == 'confirmed'], pretalx_client, event_slug)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json_data)


def get_confirmed_talks_as_json(
    pretalx_client: PretalxClient, event_slug: str, params: dict[str, Any] | None = None
) -> str:
    """
    Get confirmed talks from pretalx and convert them to JSON (legacy function for backward compatibility).

    Args:
        pretalx_client: PretalxClient instance to fetch talk and speaker data
        event_slug: Event slug for the pretalx event
        params: Additional parameters to pass to the pretalx API

    Returns:
        A JSON string containing a list of SimpleTalk objects
    """
    return get_talks_as_json(pretalx_client, event_slug, 'confirmed', params)

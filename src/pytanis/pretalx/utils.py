"""Utilities related to Pretalx"""

from collections.abc import Iterable

import pandas as pd

from pytanis.pretalx.models import Review, Speaker, Submission


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
            Col.submission_type: sub.submission_type.en,
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

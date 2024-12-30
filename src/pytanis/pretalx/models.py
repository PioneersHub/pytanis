"""Return types of the Pretalx API

Documentation: https://docs.pretalx.org/api/resources/index.html

Attention: Quite often the API docs and the actual results of the API differ!

ToDo:
    * Find out why `extra=Extra.allow` causes mypy to fail. Seems like a bug in pydantic.
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Me(BaseModel):
    name: str
    email: str
    local: str | None = None
    timezone: str


class MultiLingualStr(BaseModel):
    # ToDo: Add here more available languages, not mentioned in the API
    model_config = ConfigDict(extra='allow')

    en: str | None = None  # we assume though that english is always given to simplify things
    de: str | None = None


class URLs(BaseModel):
    base: str
    schedule: str
    login: str
    feed: str


class Event(BaseModel):
    name: MultiLingualStr
    slug: str
    is_public: bool
    date_from: date
    date_to: date | None = None
    timezone: str
    urls: URLs


class SpeakerAvailability(BaseModel):
    # ToDo: Check the datatypes here again, not mentioned in the API
    id: int
    start: str
    end: str
    allDay: str = Field(..., alias='all_day')  # noqa: N815


class AnswerQuestionRef(BaseModel):
    id: int
    question: MultiLingualStr


class Option(BaseModel):
    id: int
    answer: MultiLingualStr


class Answer(BaseModel):
    id: int
    answer: str
    answer_file: str | None = None
    question: AnswerQuestionRef
    submission: str | None = None
    review: int | None = None
    person: str | None = None
    options: list[Option]


class SubmissionSpeaker(BaseModel):
    code: str
    name: str
    biography: str | None = None
    avatar: str | None = None
    email: str | None = None


class Speaker(SubmissionSpeaker):
    submissions: list[str]  # submission codes
    availabilities: list[SpeakerAvailability] | None = None  # maybe needs organizer permissions?
    answers: list[Answer] | None = None  # maybe needs organizer permissions?


class Slot(BaseModel):
    start: datetime | None
    end: datetime | None
    room: MultiLingualStr | None
    room_id: int | None


class Resource(BaseModel):
    resource: str
    description: str


class State(Enum):
    submitted = 'submitted'
    accepted = 'accepted'
    rejected = 'rejected'  # is "Not accepted" in WebUI
    confirmed = 'confirmed'
    withdrawn = 'withdrawn'
    canceled = 'canceled'
    deleted = 'deleted'


class Submission(BaseModel):
    code: str
    speakers: list[SubmissionSpeaker]
    created: datetime | None = None  # needs organizer permissions
    title: str
    submission_type: MultiLingualStr
    submission_type_id: int
    track: MultiLingualStr | None = None
    track_id: int | None = None
    state: State
    pending_state: State | None = None  # needs organizer permissions
    abstract: str
    description: str
    duration: int | None = None
    do_not_record: bool
    is_featured: bool
    content_locale: str  # e.g. "de", "en"
    slot: Slot | None = None  # only available after schedule_web release
    slot_count: int
    image: str | None = None
    answers: list[Answer] | None = None  # needs organizer permissions and `questions` query parameter
    notes: str | None = None  # needs organizer permissions
    internal_notes: str | None = None  # needs organizer permissions
    resources: list[Resource]
    tags: list[str] | None = None  # needs organizer permissions
    tag_ids: list[int] | None = None  # needs organizer permissions


class Talk(Submission):
    pass


class User(BaseModel):
    name: str
    email: str


class Review(BaseModel):
    id: int
    submission: str
    user: str
    text: str | None = None
    score: float | None = None  # converted from str if present
    created: datetime
    updated: datetime
    answers: list[str]  # ToDo: Check this type


class RoomAvailability(BaseModel):
    start: datetime
    end: datetime


class Room(BaseModel):
    id: int
    name: MultiLingualStr
    description: MultiLingualStr
    capacity: int | None = None
    position: int | None = None
    speaker_info: MultiLingualStr | None = None
    availabilities: list[RoomAvailability] | None = None  # needs organizer permissions


class QuestionRequirement(Enum):
    optional = 'optional'
    required = 'required'
    after_deadline = 'after deadline'


class Question(BaseModel):
    id: int
    variant: str
    target: str
    question: MultiLingualStr
    help_text: MultiLingualStr
    question_required: QuestionRequirement
    deadline: datetime | None = None
    required: bool
    read_only: bool | None = None
    freeze_after: datetime | None = None
    options: list[Option]
    default_answer: str | None = None
    contains_personal_data: bool
    min_length: int | None = None
    max_length: int | None = None
    is_public: bool
    is_visible_to_reviewers: bool


class Tag(BaseModel):
    tag: str
    description: MultiLingualStr
    color: str

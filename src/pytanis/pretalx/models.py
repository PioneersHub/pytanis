"""Return types of the Pretalx API

Documentation: https://docs.pretalx.org/api/resources/index.html

Attention: Quite often the API docs and the actual results of the API differ!

ToDo:
    * Find out why `extra=Extra.allow` causes mypy to fail. Seems like a bug in pydantic.
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    """Event model for Pretalx API.

    Note: The 'urls' field was present in older API versions but is no longer
    provided by the API as of v1/v2. It's kept as optional for backward compatibility.
    """

    name: MultiLingualStr
    slug: str
    is_public: bool
    date_from: date
    date_to: date | None = None
    timezone: str
    urls: URLs | None = None  # Made optional - not provided in new API


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
    options: list[Option] | None = None


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
    start: datetime | None = None
    end: datetime | None = None
    room: MultiLingualStr | None = None
    room_id: int | None = None


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


class TransSubmissionType(BaseModel):
    """Model to keep previous and new models aligned due to changes in API v1"""

    model_config = ConfigDict(extra='allow')
    id: int
    name: MultiLingualStr


class Submission(BaseModel):
    """
    Pretalx introduced breaking API changes in 06/2025 with API "v1":
    - submission_type changed: TempSubmissionType can handle this now,
      a validator will mangel the data back to the old format MultiLingualStr
    - submission_type_id: no longer exists, will be set via submission_type now
    - is_featured is documented but does not show, defaults to False now
    """

    code: str
    speakers: list[SubmissionSpeaker]
    created: datetime | None = None  # needs organizer permissions
    title: str
    submission_type: TransSubmissionType | MultiLingualStr
    submission_type_id: int | None = None  # moved in API v1, will be set automatically for compatibility
    track: MultiLingualStr | None = None
    track_id: int | None = None
    state: State
    pending_state: State | None = None  # needs organizer permissions
    abstract: str
    description: str
    duration: int | None = None
    do_not_record: bool
    is_featured: bool
    slot: Slot | None = None  # only available after schedule_web release
    slot_count: int
    image: str | None = None
    answers: list[Answer] | None = None  # needs organizer permissions and `questions` query parameter
    notes: str | None = None  # needs organizer permissions
    internal_notes: str | None = None  # needs organizer permissions
    resources: list[Resource]
    tags: list[str] | None = None  # needs organizer permissions
    tag_ids: list[int] | None = None  # needs organizer permissions

    @model_validator(mode='after')
    def mangle_submission_type(self):
        """This is required to handle changes introduced via API v1"""
        if self.submission_type:
            self.submission_type_id = getattr(self.submission_type, 'id', None)
            self.submission_type = getattr(self.submission_type, 'name', None)
        return self


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


class QuestionSimple(BaseModel):
    """Subset of questions that are used for nested responses, e.g., in Submission.answers
    Question is the full model that is used in the questions endpoint
    """

    id: int
    variant: str
    target: str
    question: MultiLingualStr
    help_text: MultiLingualStr
    question_required: QuestionRequirement
    deadline: datetime | None = None
    required: bool = False  # default value since API v1
    read_only: bool | None = None
    freeze_after: datetime | None = None
    options: list[Option]
    default_answer: str | None = None
    contains_personal_data: bool
    min_length: int | None = None
    max_length: int | None = None
    is_public: bool
    is_visible_to_reviewers: bool

    @model_validator(mode='after')
    def is_required(self):
        if self.question_required and self.question_required != QuestionRequirement.optional:
            self.required = True
        else:
            self.required = False
        return self


class Question(QuestionSimple):
    """
    Pretalx introduced breaking API changes in 06/2025 with API "v1":
    These are the extra attributes that are provide via the questions endpoint
    but noct in the subdocuments in e.g., submissions
    """

    contains_personal_data: bool
    is_public: bool
    is_visible_to_reviewers: bool


class Tag(BaseModel):
    tag: str
    description: MultiLingualStr
    color: str


class SimpleTalk(BaseModel):
    """Simplified Talk model for generating JSON output

    This model contains only the essential information needed for display purposes.
    """

    code: str = ''  # talk code
    title: str
    speaker: str = ''  # speaker name, multiple speakers separated by comma
    organisation: str = ''  # company/institute, if multiple but similar use only one
    track: str = ''  # track
    domain_level: str = ''  # Expected audience expertise: Domain
    python_level: str = ''  # Expected audience expertise: Python
    duration: str = ''  # duration
    abstract: str = ''  # abstract of the talk
    description: str = ''  # detailed description
    prerequisites: str = ''  # prerequisites from question


class SubmissionType(BaseModel):
    """Submission type model for internal use in caching"""

    id: int
    name: MultiLingualStr
    default_duration: int | None = None


class Track(BaseModel):
    """Track model for internal use in caching"""

    id: int
    name: MultiLingualStr
    description: MultiLingualStr | None = None
    color: str | None = None

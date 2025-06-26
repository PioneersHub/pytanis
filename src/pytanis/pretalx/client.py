"""Client for the Pretalx API

Documentation: https://docs.pretalx.org/api/resources/index.html

ToDo:
    * add additional parameters explicitly like querying according to the API
"""

from collections.abc import Iterator
from http import HTTPStatus
from typing import Any, TypeAlias, TypeVar, cast

import httpx
from httpx import URL, QueryParams, Response
from pydantic import BaseModel
from structlog import get_logger
from tqdm.auto import tqdm

from pytanis.config import Config, get_cfg
from pytanis.pretalx.models import (
    Answer,
    Event,
    Me,
    Question,
    Review,
    Room,
    Speaker,
    Submission,
    SubmissionType,
    Tag,
    Talk,
    Track,
)
from pytanis.utils import rm_keys, throttle

_logger = get_logger()

T = TypeVar('T', bound=BaseModel)
JSONObj: TypeAlias = dict[str, Any]
"""Type of a JSON object (without recursion)"""
JSONLst: TypeAlias = list[JSONObj]
"""Type of a JSON list of JSON objects"""
JSON: TypeAlias = JSONObj | JSONLst
"""Type of the JSON response as returned by the Pretalx API"""


class PretalxClient:
    """Client for the Pretalx API"""

    def __init__(self, config: Config | None = None, *, blocking: bool = False):
        if config is None:
            config = get_cfg()
        self._config = config
        self._get_throttled = self._get
        self.blocking = blocking
        self.set_throttling(calls=2, seconds=1)  # we are nice by default and Pretalx doesn't allow many calls at once.

        # Caches for expanded objects (session-only, not persisted)
        self._speaker_cache: dict[str, dict] = {}
        self._submission_type_cache: dict[int, dict] = {}
        self._track_cache: dict[int, dict] = {}
        self._answer_cache: dict[int, dict | None] = {}
        self._question_cache: dict[int, dict] = {}
        self._caches_populated: dict[str, bool] = {}  # Track which event caches are populated
        self._use_cache_prepopulation: bool = True  # Enable cache pre-population by default

    def set_throttling(self, calls: int, seconds: int):
        """Throttle the number of calls per seconds to the Pretalx API"""
        _logger.info('throttling', calls=calls, seconds=seconds)
        self._get_throttled = throttle(calls, seconds)(self._get)

    def set_cache_prepopulation(self, enabled: bool) -> None:  # noqa: FBT001
        """Enable or disable automatic cache pre-population for submissions.

        When enabled (default), the client will fetch all speakers, submission types,
        and tracks in bulk on the first submission to minimize API calls.
        Disable this if you're only fetching a few submissions.

        Args:
            enabled: Whether to enable cache pre-population
        """
        self._use_cache_prepopulation = enabled
        _logger.info(f'Cache pre-population {"enabled" if enabled else "disabled"}')

    def clear_caches(self) -> None:
        """Clear all session caches.

        This is useful if you want to force fresh data to be fetched from the API.
        Note that caches are session-only and are not persisted between client instances.
        """
        self._speaker_cache.clear()
        self._submission_type_cache.clear()
        self._track_cache.clear()
        self._answer_cache.clear()
        self._question_cache.clear()
        self._caches_populated.clear()
        _logger.info('All caches cleared')

    def _get(self, endpoint: str, params: QueryParams | dict | None = None) -> Response:
        """Retrieve data via GET request"""
        if params is None:
            params = cast(QueryParams, {})

        # Build headers
        headers = {'Pretalx-Version': self._config.Pretalx.api_version}

        # Add auth if token is available
        if (api_token := self._config.Pretalx.api_token) is not None:
            headers['Authorization'] = f'Token {api_token}'

        url = URL('https://pretalx.com/').join(endpoint).copy_merge_params(params)
        _logger.info(f'GET: {url}')
        # we set the timeout to 60 seconds as the Pretalx API is quite slow
        return httpx.get(url, timeout=60.0, headers=headers, follow_redirects=True)

    def _get_one(self, endpoint: str, params: QueryParams | dict | None = None) -> JSON:
        """Retrieve a single resource result"""
        resp = self._get_throttled(endpoint, params)
        resp.raise_for_status()
        return resp.json()

    def _resolve_pagination(self, resp: JSONObj) -> Iterator[JSONObj]:
        """Resolves the pagination and returns an iterator over all results"""
        yield from resp['results']
        while (next_page := resp['next']) is not None:
            endpoint = URL(next_page).path
            resp = cast(JSONObj, self._get_one(endpoint, URL(next_page).params))
            _log_resp(resp)
            yield from resp['results']

    def _get_many(self, endpoint: str, params: QueryParams | dict | None = None) -> tuple[int, Iterator[JSONObj]]:
        """Retrieves the result count as well as the results as iterator"""
        resp = self._get_one(endpoint, params)
        _log_resp(resp)
        if isinstance(resp, list):
            return len(resp), iter(resp)
        elif self.blocking:
            _logger.debug('blocking resolution of pagination...')
            return resp['count'], iter(list(tqdm(self._resolve_pagination(resp), total=resp['count'])))
        else:
            _logger.debug('non-blocking resolution of pagination...')
            return resp['count'], self._resolve_pagination(resp)

    @classmethod
    def _expand(cls, resource, params: QueryParams | dict | None) -> QueryParams:
        """
        Since the introduction of the versioned API v1 in June 2025 an extra expand parameter is required
         to receive subdocuments that were previously included.
         For compatibility, we always expand all required to fit our models.
        """
        # For submissions, always use full expansion by default unless explicitly overridden
        params_ = dict(params) if isinstance(params, QueryParams | dict) else {}

        expanders = {
            'submissions': (
                'answers,answers.question,answers.options,resources,slots,slots.room,'
                'speakers,speakers.answers,speakers.answers.options,submission_type,tags,track'
            ),
            'speakers': 'answers,answers.question,answers.question',
            # speakers: for consistency to before API v1 we do not expand 'submissions' as well
            'questions': 'options,submission_types,tracks',
            'question-options': 'question,question.submission_types,question.tracks',
            'answers': 'options,question,question.submission_types,question.tracks',
            'teams': 'invites,limit_tracks,members',
        }
        if (params is None or 'expand' not in params) and resource in expanders:
            # Always use full expansion by default unless explicitly overridden by providing params
            params_['expand'] = expanders[resource]
        params = QueryParams(params_)
        return params

    def _endpoint_lst(
        self,
        type: type[T],  # noqa: A002
        event_slug: str,
        resource: str,
        *,
        params: QueryParams | dict | None = None,
    ) -> tuple[int, Iterator[T]]:
        """Queries an endpoint returning a list of resources"""
        endpoint = f'/api/events/{event_slug}/{resource}/'
        params = self._expand(resource, params)
        count, results = self._get_many(endpoint, params)

        results_ = []
        for result in results:
            validate = self.__validate(type, result)
            if validate:
                results_.append(validate)
        # the generator does not have a benefit, the result is loaded already anyway, kept for consistency
        return count, iter(results_)

    def _endpoint_id(
        self,
        type: type[T],  # noqa: A002
        event_slug: str,
        resource: str,
        id: int | str,  # noqa: A002
        *,
        params: QueryParams | dict | None = None,
    ) -> T:
        """Query an endpoint returning a single resource"""
        endpoint = f'/api/events/{event_slug}/{resource}/{id}/'
        params = self._expand(resource, params)
        result = self._get_one(endpoint, params)
        _logger.debug('result', resp=result)

        return self.__validate(type, result)

    @classmethod
    def me(cls) -> Me:
        """Returns what Pretalx knows about myself"""
        # removed in API update v1
        msg = 'This endpoint is no longer provided since API v1.'
        raise RuntimeError(msg)

    def event(self, event_slug: str, *, params: QueryParams | dict | None = None) -> Event:
        """Returns detailed information about a specific event"""
        endpoint = f'/api/events/{event_slug}/'
        result = self._get_one(endpoint, params)
        _logger.debug('result', resp=result)
        return self.__validate(Event, result)

    def events(self, *, params: QueryParams | dict | None = None) -> tuple[int, Iterator[Event]]:
        """Lists all events and their details"""
        count, results = self._get_many('/api/events/', params)
        events = iter(_logger.debug('result', resp=r) or Event.model_validate(r) for r in results)
        return count, events

    def submission(self, event_slug: str, code: str, *, params: QueryParams | dict | None = None) -> Submission:
        """Returns a specific submission"""
        return self._endpoint_id(Submission, event_slug, 'submissions', code, params=params)

    def submissions(
        self, event_slug: str, *, params: QueryParams | dict | None = None
    ) -> tuple[int, Iterator[Submission]]:
        """Lists all submissions and their details"""
        return self._endpoint_lst(Submission, event_slug, 'submissions', params=params)

    def talk(self, event_slug: str, code: str, *, params: QueryParams | dict | None = None) -> Talk:
        """Returns a specific talk"""
        try:
            return self._endpoint_id(Talk, event_slug, 'talks', code, params=params)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == HTTPStatus.NOT_FOUND:
                _logger.info('talk endpoint not available, using submission endpoint')
                # Use submission endpoint but validate as Talk object
                return self._endpoint_id(Talk, event_slug, 'submissions', code, params=params)
            raise

    def talks(self, event_slug: str, *, params: QueryParams | dict | None = None) -> tuple[int, Iterator[Talk]]:
        """Lists all talks and their details"""
        try:
            return self._endpoint_lst(Talk, event_slug, 'talks', params=params)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == HTTPStatus.NOT_FOUND:
                _logger.info('talks endpoint not available, using submissions endpoint')
                # Use submissions endpoint but validate as Talk objects
                return self._endpoint_lst(Talk, event_slug, 'submissions', params=params)
            raise

    def speaker(self, event_slug: str, code: str, *, params: QueryParams | dict | None = None) -> Speaker:
        """Returns a specific speaker"""
        return self._endpoint_id(Speaker, event_slug, 'speakers', code, params=params)

    def speakers(self, event_slug: str, *, params: QueryParams | dict | None = None) -> tuple[int, Iterator[Speaker]]:
        """Lists all speakers and their details"""
        return self._endpoint_lst(Speaker, event_slug, 'speakers', params=params)

    def review(self, event_slug: str, id: int, *, params: QueryParams | dict | None = None) -> Review:  # noqa: A002
        """Returns a specific review"""
        return self._endpoint_id(Review, event_slug, 'reviews', id, params=params)

    def reviews(self, event_slug: str, *, params: QueryParams | dict | None = None) -> tuple[int, Iterator[Review]]:
        """Lists all reviews and their details"""
        return self._endpoint_lst(Review, event_slug, 'reviews', params=params)

    def room(self, event_slug: str, id: int, *, params: QueryParams | dict | None = None) -> Room:  # noqa: A002
        """Returns a specific room"""
        return self._endpoint_id(Room, event_slug, 'rooms', id, params=params)

    def rooms(self, event_slug: str, *, params: QueryParams | dict | None = None) -> tuple[int, Iterator[Room]]:
        """Lists all rooms and their details"""
        return self._endpoint_lst(Room, event_slug, 'rooms', params=params)

    def question(self, event_slug: str, id: int, *, params: QueryParams | dict | None = None) -> Question:  # noqa: A002
        """Returns a specific question"""
        return self._endpoint_id(Question, event_slug, 'questions', id, params=params)

    def questions(self, event_slug: str, *, params: QueryParams | dict | None = None) -> tuple[int, Iterator[Question]]:
        """Lists all questions and their details"""
        return self._endpoint_lst(Question, event_slug, 'questions', params=params)

    def answer(self, event_slug: str, id: int, *, params: QueryParams | dict | None = None) -> Answer:  # noqa: A002
        """Returns a specific answer"""
        return self._endpoint_id(Answer, event_slug, 'answers', id, params=params)

    def answers(self, event_slug: str, *, params: QueryParams | dict | None = None) -> tuple[int, Iterator[Answer]]:
        """Lists all answers and their details"""
        return self._endpoint_lst(Answer, event_slug, 'answers', params=params)

    def tag(self, event_slug: str, tag: str, *, params: QueryParams | dict | None = None) -> Tag:
        """Returns a specific tag"""
        return self._endpoint_id(Tag, event_slug, 'tags', tag, params=params)

    def tags(self, event_slug: str, *, params: QueryParams | dict | None = None) -> tuple[int, Iterator[Tag]]:
        """Lists all tags and their details"""
        return self._endpoint_lst(Tag, event_slug, 'tags', params=params)

    def submission_type(self, event_slug: str, id: int, *, params: QueryParams | dict | None = None) -> SubmissionType:  # noqa: A002
        """Returns a specific submission type"""
        return self._endpoint_id(SubmissionType, event_slug, 'submission-types', id, params=params)

    def submission_types(
        self, event_slug: str, *, params: QueryParams | dict | None = None
    ) -> tuple[int, Iterator[SubmissionType]]:
        """Lists all submission types and their details"""
        return self._endpoint_lst(SubmissionType, event_slug, 'submission-types', params=params)

    def track(self, event_slug: str, id: int, *, params: QueryParams | dict | None = None) -> Track:  # noqa: A002
        """Returns a specific track"""
        return self._endpoint_id(Track, event_slug, 'tracks', id, params=params)

    def tracks(self, event_slug: str, *, params: QueryParams | dict | None = None) -> tuple[int, Iterator[Track]]:
        """Lists all tracks and their details"""
        return self._endpoint_lst(Track, event_slug, 'tracks', params=params)

    @classmethod
    def __validate(cls, model_type, result):
        try:
            validated = model_type.model_validate(result)
            return validated
        except Exception as e:
            # introduced to deal with API changes
            _logger.error('result', resp=e)


def _log_resp(json_resp: list[Any] | dict[Any, Any]):
    """Log everything except of the actual 'results'"""
    if isinstance(json_resp, dict):
        _logger.debug(f'response: {rm_keys("results", json_resp)}')

"""Client for the Pretalx API

Documentation: https://docs.pretalx.org/api/resources/index.html

ToDo:
    * add additional parameters explicitly like querying according to the API
"""

from collections.abc import Iterator
from typing import Any, TypeAlias, TypeVar, cast

import httpx
from httpx import URL, QueryParams, Response
from httpx_auth import HeaderApiKey
from pydantic import BaseModel
from structlog import get_logger
from tqdm.auto import tqdm

from pytanis.config import Config, get_cfg
from pytanis.pretalx.models import Answer, Event, Me, Question, Review, Room, Speaker, Submission, Tag, Talk
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

    def set_throttling(self, calls: int, seconds: int):
        """Throttle the number of calls per seconds to the Pretalx API"""
        _logger.info('throttling', calls=calls, seconds=seconds)
        self._get_throttled = throttle(calls, seconds)(self._get)

    def _get(self, endpoint: str, params: QueryParams | None = None) -> Response:
        """Retrieve data via GET request"""
        if params is None:
            params = cast(QueryParams, {})
        if (api_token := self._config.Pretalx.api_token) is None:
            msg = 'API token for Pretalx is empty'
            raise RuntimeError(msg)
        auth = HeaderApiKey(api_token, header_name='Authorization')
        url = URL('https://pretalx.com/').join(endpoint).copy_merge_params(params)
        _logger.info(f'GET: {url}')
        # we set the timeout to 60 seconds as the Pretalx API is quite slow
        headers = {'Pretalx-Version': self._config.Pretalx.api_version}
        return httpx.get(url, auth=auth, timeout=60.0, headers=headers)

    def _get_one(self, endpoint: str, params: QueryParams | None = None) -> JSON:
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

    def _get_many(self, endpoint: str, params: QueryParams | None = None) -> tuple[int, Iterator[JSONObj]]:
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

    def _endpoint_lst(
        self,
        type: type[T],  # noqa: A002
        event_slug: str,
        resource: str,
        *,
        params: QueryParams | None = None,
    ) -> tuple[int, Iterator[T]]:
        """Queries an endpoint returning a list of resources"""
        endpoint = f'/api/events/{event_slug}/{resource}/'
        count, results = self._get_many(endpoint, params)
        results_ = []
        for result in results:
            try:
                validated = type.model_validate(result)
                results_.append(validated)
            except Exception as e:
                # introduced to deal with API changes
                _logger.error('result', resp=e)
        # the generator does not have a benefit, the result is loaded already anyway, kept for consistency
        return count, iter(results_)

    def _endpoint_id(
        self,
        type: type[T],  # noqa: A002
        event_slug: str,
        resource: str,
        id: int | str,  # noqa: A002
        *,
        params: QueryParams | None = None,
    ) -> T:
        """Query an endpoint returning a single resource"""
        endpoint = f'/api/events/{event_slug}/{resource}/{id}/'
        result = self._get_one(endpoint, params)
        _logger.debug('result', resp=result)
        return type.model_validate(result)

    def me(self) -> Me:
        """Returns what Pretalx knows about myself"""
        result = self._get_one('/api/me')
        return Me.model_validate(result)

    def event(self, event_slug: str, *, params: QueryParams | None = None) -> Event:
        """Returns detailed information about a specific event"""
        endpoint = f'/api/events/{event_slug}/'
        result = self._get_one(endpoint, params)
        _logger.debug('result', resp=result)
        return Event.model_validate(result)

    def events(self, *, params: QueryParams | None = None) -> tuple[int, Iterator[Event]]:
        """Lists all events and their details"""
        count, results = self._get_many('/api/events/', params)
        events = iter(_logger.debug('result', resp=r) or Event.model_validate(r) for r in results)
        return count, events

    def submission(self, event_slug: str, code: str, *, params: QueryParams | None = None) -> Submission:
        """Returns a specific submission"""
        return self._endpoint_id(Submission, event_slug, 'submissions', code, params=params)

    def submissions(self, event_slug: str, *, params: QueryParams | None = None) -> tuple[int, Iterator[Submission]]:
        """Lists all submissions and their details"""
        return self._endpoint_lst(Submission, event_slug, 'submissions', params=params)

    def talk(self, event_slug: str, code: str, *, params: QueryParams | None = None) -> Talk:
        """Returns a specific talk"""
        return self._endpoint_id(Talk, event_slug, 'talks', code, params=params)

    def talks(self, event_slug: str, *, params: QueryParams | None = None) -> tuple[int, Iterator[Talk]]:
        """Lists all talks and their details"""
        return self._endpoint_lst(Talk, event_slug, 'talks', params=params)

    def speaker(self, event_slug: str, code: str, *, params: QueryParams | None = None) -> Speaker:
        """Returns a specific speaker"""
        return self._endpoint_id(Speaker, event_slug, 'speakers', code, params=params)

    def speakers(self, event_slug: str, *, params: QueryParams | None = None) -> tuple[int, Iterator[Speaker]]:
        """Lists all speakers and their details"""
        return self._endpoint_lst(Speaker, event_slug, 'speakers', params=params)

    def review(self, event_slug: str, id: int, *, params: QueryParams | None = None) -> Review:  # noqa: A002
        """Returns a specific review"""
        return self._endpoint_id(Review, event_slug, 'reviews', id, params=params)

    def reviews(self, event_slug: str, *, params: QueryParams | None = None) -> tuple[int, Iterator[Review]]:
        """Lists all reviews and their details"""
        return self._endpoint_lst(Review, event_slug, 'reviews', params=params)

    def room(self, event_slug: str, id: int, *, params: QueryParams | None = None) -> Room:  # noqa: A002
        """Returns a specific room"""
        return self._endpoint_id(Room, event_slug, 'rooms', id, params=params)

    def rooms(self, event_slug: str, *, params: QueryParams | None = None) -> tuple[int, Iterator[Room]]:
        """Lists all rooms and their details"""
        return self._endpoint_lst(Room, event_slug, 'rooms', params=params)

    def question(self, event_slug: str, id: int, *, params: QueryParams | None = None) -> Question:  # noqa: A002
        """Returns a specific question"""
        return self._endpoint_id(Question, event_slug, 'questions', id, params=params)

    def questions(self, event_slug: str, *, params: QueryParams | None = None) -> tuple[int, Iterator[Question]]:
        """Lists all questions and their details"""
        return self._endpoint_lst(Question, event_slug, 'questions', params=params)

    def answer(self, event_slug: str, id: int, *, params: QueryParams | None = None) -> Answer:  # noqa: A002
        """Returns a specific answer"""
        return self._endpoint_id(Answer, event_slug, 'answers', id, params=params)

    def answers(self, event_slug: str, *, params: QueryParams | None = None) -> tuple[int, Iterator[Answer]]:
        """Lists all answers and their details"""
        return self._endpoint_lst(Answer, event_slug, 'answers', params=params)

    def tag(self, event_slug: str, tag: str, *, params: QueryParams | None = None) -> Tag:
        """Returns a specific tag"""
        return self._endpoint_id(Tag, event_slug, 'tags', tag, params=params)

    def tags(self, event_slug: str, *, params: QueryParams | None = None) -> tuple[int, Iterator[Tag]]:
        """Lists all tags and their details"""
        return self._endpoint_lst(Tag, event_slug, 'tags', params=params)


def _log_resp(json_resp: list[Any] | dict[Any, Any]):
    """Log everything except of the actual 'results'"""
    if isinstance(json_resp, dict):
        _logger.debug(f'response: {rm_keys("results", json_resp)}')

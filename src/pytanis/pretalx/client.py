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

# HTTP Status codes
HTTP_NOT_FOUND = 404
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403


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

        # Caches for expanded objects
        self._speaker_cache: dict[str, dict] = {}
        self._submission_type_cache: dict[int, dict] = {}
        self._track_cache: dict[int, dict] = {}
        self._answer_cache: dict[int, dict | None] = {}
        self._question_cache: dict[int, dict] = {}

    def set_throttling(self, calls: int, seconds: int):
        """Throttle the number of calls per seconds to the Pretalx API"""
        _logger.info('throttling', calls=calls, seconds=seconds)
        self._get_throttled = throttle(calls, seconds)(self._get)

    def _get(self, endpoint: str, params: QueryParams | None = None) -> Response:
        """Retrieve data via GET request"""
        if params is None:
            params = cast(QueryParams, {})

        # Build headers
        headers = {'Pretalx-Version': self._config.Pretalx.api_version}

        # Add auth if token is available
        auth = None
        if (api_token := self._config.Pretalx.api_token) is not None:
            auth = HeaderApiKey(api_token, header_name='Authorization')

        url = URL('https://pretalx.com/').join(endpoint).copy_merge_params(params)
        _logger.info(f'GET: {url}')
        # we set the timeout to 60 seconds as the Pretalx API is quite slow
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

        # Apply expansion for backward compatibility
        if resource == 'submissions':
            results = self._expand_submissions(event_slug, results)
        elif resource == 'speakers':
            results = self._expand_speakers(event_slug, results)

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

        # Apply expansion for backward compatibility on single objects
        if resource == 'submissions' and isinstance(result, dict):
            expanded = list(self._expand_submissions(event_slug, [result]))
            if expanded:
                result = expanded[0]
        elif resource == 'speakers' and isinstance(result, dict):
            expanded = list(self._expand_speakers(event_slug, [result]))
            if expanded:
                result = expanded[0]

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
        try:
            return self._endpoint_id(Talk, event_slug, 'talks', code, params=params)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == HTTP_NOT_FOUND:
                _logger.info('talk endpoint not available, using submission endpoint')
                # Use submission endpoint but validate as Talk object
                return self._endpoint_id(Talk, event_slug, 'submissions', code, params=params)
            raise

    def talks(self, event_slug: str, *, params: QueryParams | None = None) -> tuple[int, Iterator[Talk]]:
        """Lists all talks and their details"""
        try:
            return self._endpoint_lst(Talk, event_slug, 'talks', params=params)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == HTTP_NOT_FOUND:
                _logger.info('talks endpoint not available, using submissions endpoint')
                # Use submissions endpoint but validate as Talk objects
                return self._endpoint_lst(Talk, event_slug, 'submissions', params=params)
            raise

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

    # Helper methods for backward compatibility expansion

    def _expand_submissions(self, event_slug: str, submissions: Iterator[dict]) -> Iterator[dict]:
        """Expand submission references to full objects for backward compatibility"""
        for submission in submissions:
            # Expand speakers from IDs to SubmissionSpeaker objects
            if 'speakers' in submission and submission['speakers'] and isinstance(submission['speakers'][0], str):
                expanded_speakers = []
                for speaker_code in submission['speakers']:
                    speaker = self._get_speaker_details(event_slug, speaker_code)
                    # Convert to SubmissionSpeaker format expected by the model
                    expanded_speakers.append({
                        'code': speaker['code'],
                        'name': speaker['name']
                    })
                submission['speakers'] = expanded_speakers

            # Expand submission_type from ID to MultiLingualStr
            if 'submission_type' in submission and isinstance(submission['submission_type'], int):
                type_id = submission['submission_type']
                submission_type = self._get_submission_type(event_slug, type_id)
                submission['submission_type'] = submission_type.get('name', {})
                # Add back the submission_type_id field that was removed in new API
                submission['submission_type_id'] = type_id

            # Expand track from ID to MultiLingualStr
            if 'track' in submission and isinstance(submission['track'], int):
                track_id = submission['track']
                track = self._get_track(event_slug, track_id)
                submission['track'] = track.get('name', {})

            # Expand answers from IDs to Answer objects (only if questions=all was requested)
            if 'answers' in submission and submission['answers'] and isinstance(submission['answers'][0], int):
                expanded_answers = []
                for answer_id in submission['answers']:
                    answer = self._get_answer_details(event_slug, answer_id)
                    if answer is not None:  # Skip unauthorized answers
                        expanded_answers.append(answer)
                submission['answers'] = expanded_answers if expanded_answers else None

            # Add default values for fields that the model expects but API doesn't provide
            if 'is_featured' not in submission:
                submission['is_featured'] = False

            # Expand resources from IDs to Resource objects if needed
            if 'resources' in submission and submission['resources'] and isinstance(submission['resources'][0], int):
                # For now, just clear resources as we can't expand them without more API info
                submission['resources'] = []

            # Remove new fields that don't exist in the old model
            for field in ['reviews', 'assigned_reviewers', 'median_score', 'mean_score',
                         'is_anonymised', 'anonymised_data', 'invitation_token',
                         'access_code', 'review_code']:
                submission.pop(field, None)

            yield submission

    def _expand_speakers(self, event_slug: str, speakers: Iterator[dict]) -> Iterator[dict]:
        """Expand speaker references to full objects for backward compatibility"""
        for speaker in speakers:
            # Expand answers from IDs to Answer objects
            if 'answers' in speaker and speaker['answers'] and isinstance(speaker['answers'][0], int):
                expanded_answers = []
                for answer_id in speaker['answers']:
                    answer = self._get_answer_details(event_slug, answer_id)
                    if answer is not None:  # Skip unauthorized answers
                        expanded_answers.append(answer)
                speaker['answers'] = expanded_answers if expanded_answers else None

            # Remove new fields that don't exist in the old model
            for field in ['email', 'timezone', 'locale', 'has_arrived', 'avatar_url']:
                speaker.pop(field, None)

            yield speaker

    def _get_speaker_details(self, event_slug: str, speaker_code: str) -> dict:
        """Get full speaker details (cached)"""
        if speaker_code not in self._speaker_cache:
            endpoint = f'/api/events/{event_slug}/speakers/{speaker_code}/'
            self._speaker_cache[speaker_code] = cast(dict, self._get_one(endpoint))
        return self._speaker_cache[speaker_code]

    def _get_submission_type(self, event_slug: str, type_id: int) -> dict:
        """Get submission type details (cached)"""
        if type_id not in self._submission_type_cache:
            try:
                endpoint = f'/api/events/{event_slug}/submission-types/{type_id}/'
                self._submission_type_cache[type_id] = cast(dict, self._get_one(endpoint))
            except httpx.HTTPStatusError as e:
                _logger.warning(f'Cannot fetch submission type {type_id}: {e}')
                # Return a default structure
                self._submission_type_cache[type_id] = {'name': {'en': f'Type {type_id}'}}
        return self._submission_type_cache[type_id]

    def _get_track(self, event_slug: str, track_id: int) -> dict:
        """Get track details (cached)"""
        if track_id not in self._track_cache:
            try:
                endpoint = f'/api/events/{event_slug}/tracks/{track_id}/'
                self._track_cache[track_id] = cast(dict, self._get_one(endpoint))
            except httpx.HTTPStatusError as e:
                _logger.warning(f'Cannot fetch track {track_id}: {e}')
                # Return a default structure
                self._track_cache[track_id] = {'name': {'en': f'Track {track_id}'}}
        return self._track_cache[track_id]

    def _get_answer_details(self, event_slug: str, answer_id: int) -> dict | None:
        """Get answer details (cached). Returns None if unauthorized."""
        if answer_id not in self._answer_cache:
            try:
                endpoint = f'/api/events/{event_slug}/answers/{answer_id}/'
                answer = cast(dict, self._get_one(endpoint))

                # Also expand the question reference if needed
                if 'question' in answer and isinstance(answer['question'], int):
                    question_id = answer['question']
                    if question_id not in self._question_cache:
                        q_endpoint = f'/api/events/{event_slug}/questions/{question_id}/'
                        self._question_cache[question_id] = cast(dict, self._get_one(q_endpoint))

                    question = self._question_cache[question_id]
                    # Format as AnswerQuestionRef expects
                    answer['question'] = {
                        'id': question_id,
                        'question': question.get('question', {})
                    }

                self._answer_cache[answer_id] = answer
            except httpx.HTTPStatusError as e:
                if e.response.status_code in {HTTP_UNAUTHORIZED, HTTP_FORBIDDEN}:
                    _logger.debug(f'Cannot access answer {answer_id} - unauthorized')
                    self._answer_cache[answer_id] = None
                else:
                    raise
        return self._answer_cache[answer_id]


def _log_resp(json_resp: list[Any] | dict[Any, Any]):
    """Log everything except of the actual 'results'"""
    if isinstance(json_resp, dict):
        _logger.debug(f'response: {rm_keys("results", json_resp)}')

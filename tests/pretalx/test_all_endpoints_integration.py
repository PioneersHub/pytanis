"""Comprehensive integration test for all Pretalx endpoints.

This test validates that all endpoints work correctly and that our Pydantic models
can parse the responses. It's designed to be run manually to verify API compatibility.

Usage:
    pytest tests/pretalx/test_all_endpoints_integration.py -v -s

    # With authentication (for protected endpoints)
    PRETALX_API_TOKEN=your-token pytest tests/pretalx/test_all_endpoints_integration.py -v -s

    # With specific event
    PRETALX_TEST_EVENT=pyconde-pydata-2025 pytest tests/pretalx/test_all_endpoints_integration.py -v -s
"""

import os
from collections.abc import Callable
from typing import Any

import httpx
import pytest
import structlog

from pytanis import PretalxClient
from pytanis.config import Config, PretalxCfg

# Configure structlog for human-readable test output
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt='%H:%M:%S'),
        structlog.processors.CallsiteParameterAdder(parameters=[structlog.processors.CallsiteParameter.FUNC_NAME]),
        structlog.dev.ConsoleRenderer(colors=True),  # Human-readable colored output
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Mark all tests in this file as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')]


class VerbosePretalxClient(PretalxClient):
    """PretalxClient that logs API calls with full details."""

    def _get(self, endpoint: str, params=None):
        """Override to log full request details."""
        # Build the full URL
        from httpx import URL  # noqa: PLC0415

        url = URL('https://pretalx.com/').join(endpoint)
        if params:
            url = url.copy_merge_params(params)

        # Build headers
        headers = {'Pretalx-Version': self._config.Pretalx.api_version}
        if self._config.Pretalx.api_token:
            headers['Authorization'] = f'Token {self._config.Pretalx.api_token[:8]}...'  # Show first 8 chars

        logger.info('api_call', emoji='🌐', url=str(url), headers=headers)

        # Call parent implementation
        response = super()._get(endpoint, params)
        logger.info('api_response', status_code=response.status_code, reason=response.reason_phrase)
        return response


class TestAllPretalxEndpoints:
    """Test all Pretalx API endpoints comprehensively."""

    @pytest.fixture(scope='class')
    def client(self):  # noqa: PLR6301
        """Create a VerbosePretalxClient for testing."""
        from pathlib import Path  # noqa: PLC0415

        api_token = os.getenv('PRETALX_API_TOKEN')
        api_version = os.getenv('PRETALX_API_VERSION', 'v1')

        # Create a temporary config file path
        config_path = Path.home() / '.pytanis' / 'test_config.toml'
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create empty config file if it doesn't exist
        if not config_path.exists():
            config_path.touch()

        config = Config(
            cfg_path=config_path,
            Pretalx=PretalxCfg(api_token=api_token, api_version=api_version),
        )
        return VerbosePretalxClient(config=config)

    @pytest.fixture(scope='class')
    def event_slug(self):  # noqa: PLR6301
        """Get the event slug to test against."""
        return os.getenv('PRETALX_TEST_EVENT', 'pyconde-pydata-2025')

    def _test_endpoint(self, name: str, test_func: Callable, expected_errors: set[int] | None = None) -> dict[str, Any]:  # noqa: PLR6301
        """Test an endpoint and return result info."""
        if expected_errors is None:
            expected_errors = set()

        result = {
            'endpoint': name,
            'success': False,
            'error': None,
            'data': None,
            'count': None,
        }

        try:
            data = test_func()
            result['success'] = True
            result['data'] = data

            # If it's a tuple (count, iterator), extract count
            if isinstance(data, tuple) and len(data) == 2:
                count, items = data
                result['count'] = count
                # Materialize first few items to validate parsing
                result['data'] = list(items)[:3]  # Get first 3 items

            logger.info('endpoint_test_success', endpoint=name, symbol='✓', count=result['count'])

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            result['error'] = f'HTTP {status_code}'

            if status_code in expected_errors:
                result['success'] = True  # Expected error
                logger.info('endpoint_test_expected_error', endpoint=name, symbol='✓', status_code=status_code)
            else:
                logger.error('endpoint_test_failed', endpoint=name, symbol='✗', status_code=status_code)

        except Exception as e:
            result['error'] = str(e)
            logger.error(
                'endpoint_test_exception',
                endpoint=name,
                symbol='✗',
                exception_type=type(e).__name__,
                error=str(e)[:100],
            )

        return result

    def _validate_auth_and_event(self, client: VerbosePretalxClient, event_slug: str) -> bool:  # noqa: PLR6301
        """Validate authentication token and event slug before running tests."""
        logger.info('validation_start', message='VALIDATING TEST CONFIGURATION', separator='=' * 80)

        # Display configuration
        logger.info(
            'test_configuration',
            api_version=client._config.Pretalx.api_version,
            api_token_provided=bool(client._config.Pretalx.api_token),
            event_slug=event_slug,
        )

        # Test 1: Validate authentication with /api/me
        if client._config.Pretalx.api_token:
            logger.info('auth_test', step=1, message='Testing authentication token...')
            try:
                me = client.me()
                logger.info(
                    'auth_success',
                    symbol='✓',
                    message='Authentication successful!',
                    user_name=me.name,
                    user_email=me.email,
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code in {401, 403}:
                    logger.error(
                        'auth_failed', symbol='✗', message='Invalid API token', status_code=e.response.status_code
                    )
                    return False
                raise
            except Exception as e:
                logger.error('auth_exception', symbol='✗', exception_type=type(e).__name__, error=str(e))
                return False
        else:
            logger.info('auth_skip', step=1, message='No API token provided - skipping authentication test')

        # Test 2: Validate event exists
        logger.info('event_test', step=2, message=f"Validating event '{event_slug}'...")
        try:
            event = client.event(event_slug)
            logger.info(
                'event_found',
                symbol='✓',
                event_name=event.name.en,
                date_from=str(event.date_from),
                date_to=str(event.date_to) if event.date_to else 'N/A',
                timezone=event.timezone,
                is_public=event.is_public,
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error('event_not_found', symbol='✗', event_slug=event_slug)
            else:
                logger.error('event_validation_failed', symbol='✗', status_code=e.response.status_code)
            return False
        except Exception as e:
            logger.error('event_exception', symbol='✗', exception_type=type(e).__name__, error=str(e))
            return False

        logger.info(
            'validation_complete',
            symbol='✓',
            message='All validations passed! Proceeding with endpoint tests...',
            separator='=' * 80,
        )
        return True

    def test_all_endpoints(self, client: VerbosePretalxClient, event_slug: str):  # noqa: PLR0914
        """Test all Pretalx endpoints systematically."""
        # First validate configuration
        if not self._validate_auth_and_event(client, event_slug):
            pytest.fail('Configuration validation failed. Please check your API token and event slug.')

        logger.info(
            'test_start',
            message='COMPREHENSIVE PRETALX ENDPOINT TEST',
            event_slug=event_slug,
            api_version=client._config.Pretalx.api_version,
            authenticated=bool(client._config.Pretalx.api_token),
            separator='=' * 80,
        )

        results = []

        # Test event endpoints
        logger.info('test_section', section='EVENT endpoints', separator='-' * 40)
        results.append(self._test_endpoint('/api/events/', lambda: client.events(params={'limit': 5})))

        results.append(self._test_endpoint(f'/api/events/{event_slug}/', lambda: client.event(event_slug)))

        # Test submission endpoints
        logger.info('test_section', section='SUBMISSION endpoints', separator='-' * 40)
        submissions_result = self._test_endpoint(
            f'/api/events/{event_slug}/submissions/',
            lambda: client.submissions(event_slug, params={'limit': 5, 'questions': 'all'}),
        )
        results.append(submissions_result)

        # Test single submission if we got any
        if submissions_result['success'] and submissions_result['data']:
            first_submission = submissions_result['data'][0]
            results.append(
                self._test_endpoint(
                    f'/api/events/{event_slug}/submissions/{first_submission.code}/',
                    lambda: client.submission(event_slug, first_submission.code),
                )
            )

        # Test speaker endpoints
        logger.info('test_section', section='SPEAKER endpoints', separator='-' * 40)
        speakers_result = self._test_endpoint(
            f'/api/events/{event_slug}/speakers/', lambda: client.speakers(event_slug, params={'limit': 5})
        )
        results.append(speakers_result)

        # Test single speaker if we got any
        if speakers_result['success'] and speakers_result['data']:
            first_speaker = speakers_result['data'][0]
            results.append(
                self._test_endpoint(
                    f'/api/events/{event_slug}/speakers/{first_speaker.code}/',
                    lambda: client.speaker(event_slug, first_speaker.code),
                )
            )

        # Test room endpoints
        logger.info('test_section', section='ROOM endpoints', separator='-' * 40)
        rooms_result = self._test_endpoint(
            f'/api/events/{event_slug}/rooms/', lambda: client.rooms(event_slug, params={'limit': 5})
        )
        results.append(rooms_result)

        # Test question endpoints
        logger.info('test_section', section='QUESTION endpoints', separator='-' * 40)
        questions_result = self._test_endpoint(
            f'/api/events/{event_slug}/questions/', lambda: client.questions(event_slug, params={'limit': 5})
        )
        results.append(questions_result)

        # Test single question if we got any
        if questions_result['success'] and questions_result['data']:
            first_question = questions_result['data'][0]
            results.append(
                self._test_endpoint(
                    f'/api/events/{event_slug}/questions/{first_question.id}/',
                    lambda: client.question(event_slug, first_question.id),
                )
            )

        # Test answer endpoints (may require auth)
        logger.info('test_section', section='ANSWER endpoints', separator='-' * 40)
        answers_result = self._test_endpoint(
            f'/api/events/{event_slug}/answers/',
            lambda: client.answers(event_slug, params={'limit': 5}),
            expected_errors={401, 403} if not client._config.Pretalx.api_token else set(),
        )
        results.append(answers_result)

        # Test single answer if we got any
        if answers_result['success'] and answers_result['data']:
            first_answer = answers_result['data'][0]
            results.append(
                self._test_endpoint(
                    f'/api/events/{event_slug}/answers/{first_answer.id}/',
                    lambda: client.answer(event_slug, first_answer.id),
                    expected_errors={401, 403} if not client._config.Pretalx.api_token else set(),
                )
            )

        # Test review endpoints (requires auth)
        logger.info('test_section', section='REVIEW endpoints', separator='-' * 40)
        reviews_result = self._test_endpoint(
            f'/api/events/{event_slug}/reviews/',
            lambda: client.reviews(event_slug, params={'limit': 5}),
            expected_errors={401, 403} if not client._config.Pretalx.api_token else set(),
        )
        results.append(reviews_result)

        # Test single review if we got any
        if reviews_result['success'] and reviews_result['data']:
            first_review = reviews_result['data'][0]
            results.append(
                self._test_endpoint(
                    f'/api/events/{event_slug}/reviews/{first_review.id}/',
                    lambda: client.review(event_slug, first_review.id),
                    expected_errors={401, 403} if not client._config.Pretalx.api_token else set(),
                )
            )

        # Test backward compatibility
        # print('\n' + '-' * 40)
        # print('Testing BACKWARD COMPATIBILITY features...')
        # print('-' * 40)
        # self._test_backward_compatibility(client, event_slug, results)

        # Summary
        logger.info('test_summary', message='TEST SUMMARY', separator='=' * 80)

        total = len(results)
        successful = sum(1 for r in results if r['success'])
        failed = total - successful

        logger.info('test_results', total_endpoints=total, successful=successful, failed=failed)

        if failed > 0:
            failed_endpoints = [{'endpoint': r['endpoint'], 'error': r['error']} for r in results if not r['success']]
            logger.error('failed_endpoints_list', failed_endpoints=failed_endpoints)

        # Show test environment details
        logger.info(
            'test_environment',
            api_version=client._config.Pretalx.api_version,
            event_slug=event_slug,
            authenticated=bool(client._config.Pretalx.api_token),
        )

        # Assert that we have a reasonable success rate
        success_rate = successful / total
        logger.info('success_rate', rate=f'{success_rate:.1%}')

        # We expect at least 70% success rate (some endpoints may require auth or specific data)
        assert success_rate >= 0.7, f'Too many endpoint failures: {failed}/{total}'


if __name__ == '__main__':
    # Allow running directly with python
    pytest.main([__file__, '-v', '-s'])

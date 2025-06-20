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

from pytanis import PretalxClient
from pytanis.config import Config, PretalxCfg


# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class VerbosePretalxClient(PretalxClient):
    """PretalxClient that logs API calls with full details."""

    def _get(self, endpoint: str, params=None):
        """Override to log full request details."""
        # Build the full URL
        from httpx import URL

        url = URL('https://pretalx.com/').join(endpoint)
        if params:
            url = url.copy_merge_params(params)

        # Build headers
        headers = {'Pretalx-Version': self._config.Pretalx.api_version}
        if self._config.Pretalx.api_token:
            headers['Authorization'] = f'Token {self._config.Pretalx.api_token[:8]}...'  # Show first 8 chars

        print(f'\n🌐 API Call:')
        print(f'   URL: {url}')
        print(f'   Headers: {headers}')

        # Call parent implementation
        response = super()._get(endpoint, params)
        print(f'   Response: {response.status_code} {response.reason_phrase}')
        return response


class TestAllPretalxEndpoints:
    """Test all Pretalx API endpoints comprehensively."""

    @pytest.fixture(scope='class')
    def client(self):
        """Create a VerbosePretalxClient for testing."""
        from pathlib import Path

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
    def event_slug(self):
        """Get the event slug to test against."""
        return os.getenv('PRETALX_TEST_EVENT', 'pyconde-pydata-2025')

    def _test_endpoint(self, name: str, test_func: Callable, expected_errors: set[int] | None = None) -> dict[str, Any]:
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

            print(f'✓ {name}: SUCCESS', end='')
            if result['count'] is not None:
                print(f' (found {result["count"]} items)')
            else:
                print()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            result['error'] = f'HTTP {status_code}'

            if status_code in expected_errors:
                result['success'] = True  # Expected error
                print(f'✓ {name}: Expected error - HTTP {status_code}')
            else:
                print(f'✗ {name}: FAILED - HTTP {status_code}')

        except Exception as e:
            result['error'] = str(e)
            print(f'✗ {name}: FAILED - {type(e).__name__}: {str(e)[:100]}')

        return result

    def _validate_auth_and_event(self, client: VerbosePretalxClient, event_slug: str) -> bool:
        """Validate authentication token and event slug before running tests."""
        print('\n' + '=' * 80)
        print('VALIDATING TEST CONFIGURATION')
        print('=' * 80)

        # Display configuration
        print(f'\nConfiguration:')
        print(f'  API Version: {client._config.Pretalx.api_version}')
        print(f'  API Token: {"Provided" if client._config.Pretalx.api_token else "Not provided"}')
        print(f'  Event Slug: {event_slug}')

        # Test 1: Validate authentication with /api/me
        if client._config.Pretalx.api_token:
            print('\n1. Testing authentication token...')
            try:
                me = client.me()
                print(f'   ✓ Authentication successful! Logged in as: {me.name} ({me.email})')
            except httpx.HTTPStatusError as e:
                if e.response.status_code in {401, 403}:
                    print(f'   ✗ Authentication failed: Invalid API token (HTTP {e.response.status_code})')
                    return False
                raise
            except Exception as e:
                print(f'   ✗ Authentication failed: {type(e).__name__}: {str(e)}')
                return False
        else:
            print('\n1. No API token provided - skipping authentication test')

        # Test 2: Validate event exists
        print(f"\n2. Validating event '{event_slug}'...")
        try:
            event = client.event(event_slug)
            print(f'   ✓ Event found: {event.name.en}')
            print(f'     Date: {event.date_from} to {event.date_to}')
            print(f'     Timezone: {event.timezone}')
            if event.is_public:
                print('     Status: Public')
            else:
                print('     Status: Not public')
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"   ✗ Event not found: '{event_slug}' does not exist")
            else:
                print(f'   ✗ Event validation failed: HTTP {e.response.status_code}')
            return False
        except Exception as e:
            print(f'   ✗ Event validation failed: {type(e).__name__}: {str(e)}')
            return False

        print('\n✓ All validations passed! Proceeding with endpoint tests...')
        print('=' * 80)
        return True

    def test_all_endpoints(self, client: VerbosePretalxClient, event_slug: str):
        """Test all Pretalx endpoints systematically."""
        # First validate configuration
        if not self._validate_auth_and_event(client, event_slug):
            pytest.fail('Configuration validation failed. Please check your API token and event slug.')

        print('\n' + '=' * 80)
        print('COMPREHENSIVE PRETALX ENDPOINT TEST')
        print(f'Event: {event_slug}')
        print(f'API Version: {client._config.Pretalx.api_version}')
        print(f'Authenticated: {"Yes" if client._config.Pretalx.api_token else "No"}')
        print('=' * 80 + '\n')

        results = []

        # Test event endpoints
        print('\n' + '-' * 40)
        print('Testing EVENT endpoints...')
        print('-' * 40)
        results.append(self._test_endpoint('/api/events/', lambda: client.events(params={'limit': 5})))

        results.append(self._test_endpoint(f'/api/events/{event_slug}/', lambda: client.event(event_slug)))

        # Test submission endpoints
        print('\n' + '-' * 40)
        print('Testing SUBMISSION endpoints...')
        print('-' * 40)
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
                    lambda: client.submission(event_slug, first_submission.code, params={'questions': 'all'}),
                )
            )


        # Test speaker endpoints
        print('\n' + '-' * 40)
        print('Testing SPEAKER endpoints...')
        print('-' * 40)
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
        print('\n' + '-' * 40)
        print('Testing ROOM endpoints...')
        print('-' * 40)
        rooms_result = self._test_endpoint(
            f'/api/events/{event_slug}/rooms/', lambda: client.rooms(event_slug, params={'limit': 5})
        )
        results.append(rooms_result)

        # Test single room if we got any
        if rooms_result['success'] and rooms_result['data']:
            first_room = rooms_result['data'][0]
            results.append(
                self._test_endpoint(
                    f'/api/events/{event_slug}/rooms/{first_room.id}/', lambda: client.room(event_slug, first_room.id)
                )
            )

        # Test question endpoints
        print('\n' + '-' * 40)
        print('Testing QUESTION endpoints...')
        print('-' * 40)
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
        print('\n' + '-' * 40)
        print('Testing ANSWER endpoints...')
        print('-' * 40)
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
        print('\n' + '-' * 40)
        print('Testing REVIEW endpoints...')
        print('-' * 40)
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
        print('\n' + '-' * 40)
        print('Testing BACKWARD COMPATIBILITY features...')
        print('-' * 40)
        self._test_backward_compatibility(client, event_slug, results)

        # Summary
        print('\n' + '=' * 80)
        print('TEST SUMMARY')
        print('=' * 80)

        total = len(results)
        successful = sum(1 for r in results if r['success'])
        failed = total - successful

        print(f'\nEndpoints Tested: {total}')
        print(f'✓ Successful: {successful}')
        print(f'✗ Failed: {failed}')

        if failed > 0:
            print('\nFailed endpoints:')
            for r in results:
                if not r['success']:
                    print(f'  - {r["endpoint"]}: {r["error"]}')

        # Show test environment details
        print(f'\nTest Environment:')
        print(f'  API Version: {client._config.Pretalx.api_version}')
        print(f'  Event: {event_slug}')
        print(f'  Authentication: {"Yes" if client._config.Pretalx.api_token else "No"}')

        # Assert that we have a reasonable success rate
        success_rate = successful / total
        print(f'\nSuccess rate: {success_rate:.1%}')

        # We expect at least 70% success rate (some endpoints may require auth or specific data)
        assert success_rate >= 0.7, f'Too many endpoint failures: {failed}/{total}'

    def _test_backward_compatibility(self, client: PretalxClient, event_slug: str, results: list):
        """Test backward compatibility features."""
        # Test that submissions have expanded speakers
        try:
            _, submissions = client.submissions(event_slug, params={'limit': 1})
            submission = next(submissions, None)

            if submission and submission.speakers:
                # Check that speakers are objects, not IDs
                speaker = submission.speakers[0]
                assert hasattr(speaker, 'name'), 'Speaker should be expanded object with name'
                assert hasattr(speaker, 'code'), 'Speaker should be expanded object with code'
                print('✓ Backward compatibility: Speaker expansion working')
                results.append({
                    'endpoint': 'Backward compat: Speaker expansion',
                    'success': True,
                })
            else:
                print('⚠ Backward compatibility: No submissions with speakers to test')

        except Exception as e:
            print(f'✗ Backward compatibility test failed: {e}')
            results.append({
                'endpoint': 'Backward compat: Speaker expansion',
                'success': False,
                'error': str(e),
            })

        # Test that submission types are expanded
        try:
            _, submissions = client.submissions(event_slug, params={'limit': 1})
            submission = next(submissions, None)

            if submission and submission.submission_type:
                # Check that submission_type is MultiLingualStr, not ID
                assert hasattr(submission.submission_type, 'en'), 'Submission type should be MultiLingualStr'
                assert hasattr(submission, 'submission_type_id'), 'Should have submission_type_id field'
                print('✓ Backward compatibility: Submission type expansion working')
                results.append({
                    'endpoint': 'Backward compat: Submission type expansion',
                    'success': True,
                })
            else:
                print('⚠ Backward compatibility: No submissions with types to test')

        except Exception as e:
            print(f'✗ Backward compatibility test failed: {e}')
            results.append({
                'endpoint': 'Backward compat: Submission type expansion',
                'success': False,
                'error': str(e),
            })


if __name__ == '__main__':
    # Allow running directly with python
    pytest.main([__file__, '-v', '-s'])

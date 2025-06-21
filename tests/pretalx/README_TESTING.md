# Pretalx Testing Strategy

This document describes the testing approach for Pretalx API integration in pytanis.

## Test Categories

### 1. Unit Tests (`test_client.py`)
Tests basic functionality with the Pretalx API. These tests are divided into:

- **Public Endpoints** (always tested):
  - Events listing and details
  - Submissions listing and details
  - Speakers listing and details
  - Rooms listing and details
  - Questions listing
  - Submission types
  - Tracks

- **Authenticated Endpoints** (require special permissions):
  - Reviews (requires organizer permissions)
  - Answers (requires organizer permissions)
  - Tags (requires organizer permissions)

  These tests are automatically skipped unless `PRETALX_API_TOKEN` environment variable is set with a token that has proper permissions.

### 2. Integration Tests

#### `test_integration.py`
- Tests Pydantic model validation with live API data
- Uses public endpoints only
- Works with or without authentication

#### `test_integration_with_token.py`
- Comprehensive model validation requiring authentication
- Tests all Pydantic models including auth-required ones
- Skipped entirely when `PRETALX_API_TOKEN` is not set

#### `test_all_endpoints_integration.py`
- Tests all API endpoints comprehensively
- Provides detailed logging of API calls
- Requires `PRETALX_API_TOKEN` for full coverage

#### `test_submission_integration.py`
- Tests the Submission model with API v1 compatibility
- Tests SimpleTalk conversion and JSON export
- Works with public data

## Authentication Handling

Tests check for authentication in this order:

1. **Environment Variable** (`PRETALX_API_TOKEN`): Highest priority
   - Used by integration tests requiring auth
   - Required for auth-endpoint tests in `test_client.py`

2. **Local Config** (`~/.pytanis/config.toml`): Used automatically
   - PretalxClient() without config uses this if available
   - May not have permissions for all endpoints

3. **Test Config** (`tests/cfgs/config.toml`): For CI/CD
   - Contains dummy tokens
   - Used when `tmp_config` fixture is active

## Running Tests

### Run all tests:
```bash
hatch run no-cov
```

### Run specific test categories:
```bash
# Unit tests only
hatch run pytest tests/pretalx/test_client.py

# Integration tests with token
PRETALX_API_TOKEN=your_token hatch run pytest tests/pretalx/test_integration_with_token.py

# All endpoints test
PRETALX_API_TOKEN=your_token hatch run test-endpoints
```

### Skip conditions:
- Tests marked with `@pytest.mark.skipif(os.getenv('GITHUB'), reason='on Github')` are skipped in CI
- Auth-required tests are skipped without proper `PRETALX_API_TOKEN`
- Integration tests requiring token are skipped without the env var

## Test Fixtures

- `pretalx_client`: Basic client, uses local config if available
- `authenticated_client`: Client with test config (uses `tmp_config`)
- `tmp_config`: Sets up test configuration environment

## Adding New Tests

1. For public endpoints: Add to appropriate test file, use `pretalx_client` fixture
2. For auth endpoints: Add `@requires_auth` decorator, document permissions needed
3. For integration tests: Consider if auth is required, add appropriate skip conditions

## Troubleshooting

- **401 Unauthorized**: Token missing or lacks permissions for endpoint
- **Tests not skipping**: Check skip conditions match your test requirements
- **Import errors**: Ensure proper relative imports within test modules

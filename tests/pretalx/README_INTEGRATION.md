# Pretalx Integration Tests

This directory contains integration tests that validate all Pydantic models against live Pretalx API data.

## Purpose

The integration tests ensure that:
1. All Pydantic models correctly parse real API responses
2. Model relationships are consistent (e.g., speaker references in submissions)
3. Optional fields are handled properly
4. Edge cases like empty collections are handled gracefully

## Running the Tests

### Using Hatch (Recommended for Development)

If you're developing Pytanis, use Hatch commands for a properly configured environment:

```bash
# Interactive mode
hatch run integration

# With arguments
hatch run integration --token YOUR_TOKEN --event pyconde-pydata-2025

# Quick mode with environment variables
export PRETALX_API_TOKEN="your-token"
export PRETALX_TEST_EVENT="pyconde-pydata-2025"
hatch run integration-quick

# Direct pytest access
hatch run test-endpoints
```

### Interactive CLI (Recommended)

The easiest way to run integration tests is using the interactive CLI:

```bash
# From project root
python run_pretalx_integration_tests.py

# Or from tests directory
python tests/pretalx/run_integration_tests.py
```

This will:
- Prompt you for API token (optional but recommended)
- Prompt you for event slug
- Confirm settings before running
- Run the comprehensive integration tests

### CLI with Arguments

```bash
# Run with token and event
python run_pretalx_integration_tests.py --token YOUR_TOKEN --event pyconde-pydata-2025

# Run with specific API version
python run_pretalx_integration_tests.py --token YOUR_TOKEN --event pyconde-pydata-2025 --api-version v2

# Run specific test
python run_pretalx_integration_tests.py --token YOUR_TOKEN --event EVENT --test test_all_endpoints

# Show help
python run_pretalx_integration_tests.py --help
```

### Direct pytest Usage

### Run all integration tests
```bash
pytest tests/pretalx/test_integration.py -v
```

### Run integration tests with existing tests
```bash
pytest -m integration
```

### Skip integration tests
```bash
pytest -m "not integration"
```

### Using environment variables
```bash
# Skip all integration tests
SKIP_INTEGRATION_TESTS=true pytest

# Use authenticated API access (recommended for full coverage)
PRETALX_API_TOKEN=your-token-here pytest -m integration

# Test against a specific event
PRETALX_TEST_EVENT=your-event-slug pytest -m integration

# Use a different Pretalx instance
PRETALX_API_URL=https://your-instance.com/api pytest -m integration
```

## Test Coverage

The integration tests validate the following models:
- `Me` - User profile (requires authentication)
- `Event` - Event details and MultiLingualStr
- `Submission` - Talk submissions with speakers and answers
- `Talk` - Scheduled talks with slots and resources
- `Speaker` - Speaker profiles with availabilities
- `Room` - Conference rooms with availabilities
- `Question` - Form questions with options
- `Answer` - Responses to questions
- `Tag` - Event tags
- `Review` - Submission reviews (requires authentication)
- `SimpleTalk` - Simplified talk representation
- Supporting models: `Slot`, `Resource`, `URLs`, `Option`, etc.

## Authentication

Some endpoints require authentication:
- `/me` - User profile
- `/reviews` - Submission reviews

Without authentication, these tests will be skipped. To test authenticated endpoints, set the `PRETALX_API_TOKEN` environment variable.

## Rate Limiting

The tests are designed to be respectful of API rate limits:
- Limited number of items fetched per test
- Tests can be run against different Pretalx instances
- Failed requests are handled gracefully

## Adding New Tests

When adding new models or endpoints:
1. Add a test method to validate the model with live data
2. Include proper error handling for missing data or auth requirements
3. Test both required and optional fields
4. Validate model serialization and deserialization
5. Consider adding consistency tests for related models
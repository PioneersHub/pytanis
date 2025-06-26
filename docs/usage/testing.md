# Testing

This guide covers testing pytanis, including setup, running tests with hatch, and configuration options.

## Setup

Install pytanis with development dependencies:

```bash
# Clone the repository
git clone https://github.com/pioneershub/pytanis.git
cd pytanis

# Install with hatch (recommended)
pip install hatch
hatch env create

# Or install directly with pip
pip install -e ".[all]"
pip install pytest pytest-cov pytest-mock pytest-vcr
```

## Running Tests

### Using Hatch (Recommended)

Hatch provides pre-configured test environments:

```bash
# Run all tests with coverage
hatch run cov

# Run tests without coverage
hatch run no-cov

# Debug mode with breakpoints
hatch run debug

# Run integration tests
hatch run integration
```

### Direct pytest Usage

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=pytanis --cov-report=term-missing

# Run specific test file
pytest tests/pretalx/test_client.py

# Run tests matching pattern
pytest -k "test_event"

# Exclude integration tests
pytest -m "not integration"
```

## Configuration

### Environment Variables

When local configuration is not available or desired, use environment variables:

```bash
# Pretalx API configuration
export PRETALX_API_TOKEN="your-api-token"
export PRETALX_TEST_EVENT="event-slug"  # Default: pyconde-pydata-2025

# Run integration tests with environment variables
hatch run integration
```

### Local Configuration

Create a `config.toml` file in your project root:

```toml
[Pretalx]
api_token = "your-api-token"

[Google]
client_secret_json = "path/to/client_secret.json"
token_json = "token.json"

[HelpDesk]
account = "account-id"
entity_id = "email@example.com"
token = "helpdesk-token"
```

## Test Types

### Unit Tests

Standard tests that don't require external services:

```bash
# Run unit tests only
pytest tests/ -m "not integration"
```

### Integration Tests

Tests that interact with live APIs (marked with `@pytest.mark.integration`):

```bash
# Run integration tests only
pytest -m integration

# Or use hatch
hatch run integration
```

### Coverage Reports

Generate detailed coverage reports:

```bash
# Terminal report
hatch run cov

# HTML report
pytest --cov=pytanis --cov-report=html
# Open htmlcov/index.html in browser

# XML report for CI
hatch run ci
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_config.toml     # Test configuration
├── pretalx/
│   ├── test_client.py   # Client unit tests
│   ├── test_integration.py  # Integration tests
│   └── test_config.py   # Configuration tests
└── helpdesk/
    └── test_mail.py     # HelpDesk tests
```

## Common Commands

```bash
# Quick test during development
hatch run no-cov tests/pretalx/test_client.py

# Full test suite before commits
hatch run cov

# Integration test with custom event
PRETALX_TEST_EVENT="my-event" hatch run integration

# Debug failing test
hatch run debug tests/pretalx/test_client.py::test_specific_case
```

## Troubleshooting

### Missing Dependencies

```bash
# Ensure all test dependencies are installed
hatch env prune
hatch env create
```

### Authentication Errors

- Verify `PRETALX_API_TOKEN` is set correctly
- Check token has necessary permissions
- Ensure event slug exists and is accessible

### Slow Tests

- Use `-x` to stop on first failure
- Run specific tests with `-k pattern`
- Skip integration tests for faster feedback

### SSL/Certificate Issues

- Update system certificates
- Check corporate proxy settings
- Set `REQUESTS_CA_BUNDLE` if needed

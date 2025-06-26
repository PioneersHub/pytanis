# Testing Quick Reference

This is a quick reference for running tests in Pytanis development.

## Unit Tests

```bash
# Run all unit tests with coverage
hatch run cov

# Run tests without coverage
hatch run no-cov

# Debug tests with pdb
hatch run debug

# Run specific test file
hatch run pytest tests/pretalx/test_models.py
```

## Integration Tests

Integration tests validate the Pretalx API compatibility with real API calls.

### Prerequisites
- Valid Pretalx API token
- Event slug (e.g., `pyconde-pydata-2025`)
- Network access to Pretalx API

### Features
- **Authentication validation**: Tests your API token before running all tests
- **Event validation**: Verifies the event exists and is accessible
- **Verbose API logging**: Shows full URLs, headers, and responses for each call
- **Grouped endpoints**: Tests are organized by endpoint type (speakers, talks, etc.)
- **Detailed summary**: Shows which endpoints passed/failed with reasons

### Quick Start

```bash
# Interactive mode (will prompt for credentials)
hatch run integration

# With command-line arguments
hatch run integration --token YOUR_TOKEN --event pyconde-pydata-2025 --api-version v2

# Using environment variables
export PRETALX_API_TOKEN="your-token"
export PRETALX_TEST_EVENT="pyconde-pydata-2025"
hatch run integration-quick

# Direct pytest access for more control
hatch run test-endpoints

# Run specific integration test
hatch run test-endpoints -k test_all_endpoints
```

### Available Hatch Scripts

| Command | Description |
|---------|-------------|
| `hatch run integration` | Run integration tests interactively |
| `hatch run integration-quick` | Run with environment variables |
| `hatch run test-endpoints` | Direct pytest access to integration tests |
| `hatch run cov` | Run unit tests with coverage |
| `hatch run no-cov` | Run unit tests without coverage |
| `hatch run debug` | Debug tests with pdb |
| `hatch run lint:all` | Run all linters |
| `hatch run lint:fix` | Auto-fix linting issues |

## Environment Variables

For CI/CD or quick testing:

```bash
export PRETALX_API_TOKEN="your-api-token"
export PRETALX_TEST_EVENT="pyconde-pydata-2025"
export PRETALX_API_VERSION="v2"  # optional, defaults to v1
```

## Tips

1. **First Time**: Use `hatch run integration` for interactive setup
2. **CI/CD**: Use environment variables with `hatch run integration-quick`
3. **Debugging**: Use `hatch run test-endpoints -v -s` for verbose output
4. **Specific Tests**: Add `-k pattern` to match test names

## More Information

- Full testing guide: [docs/usage/testing.md](docs/usage/testing.md)
- Integration test details: [tests/pretalx/README_INTEGRATION.md](tests/pretalx/README_INTEGRATION.md)
- Contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)

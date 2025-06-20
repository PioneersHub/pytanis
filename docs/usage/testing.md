# Testing

Pytanis includes comprehensive testing tools to ensure compatibility with the Pretalx API. This guide covers how to use the integration tests to validate your setup and API compatibility.

## Integration Tests

The integration tests are designed to validate that all Pytanis data models work correctly with live Pretalx API responses. These tests are particularly useful:

- Before upgrading Pytanis to ensure compatibility
- When the Pretalx API changes
- To validate your API credentials and permissions
- To test against different Pretalx events or API versions

### Prerequisites

To run integration tests, you need:

1. A valid Pretalx API token
2. An event slug to test against (e.g., `pyconde-pydata-2025`)
3. Network access to the Pretalx API

### Running Integration Tests

#### Interactive Mode (Recommended)

The easiest way to run integration tests is using the interactive CLI:

```bash
# From the project root
python scripts/run_pretalx_integration_tests.py
```

This will:
1. Prompt you for your API token (securely, without displaying it)
2. Prompt you for the event slug (default: `pyconde-pydata-2025`)
3. Prompt you for the API version (default: `v1`)
4. Show your configuration and ask for confirmation
5. Run the comprehensive integration tests

Example interactive session:
```
============================================================
Pretalx Integration Test Runner
============================================================

This tool will run comprehensive integration tests against the Pretalx API.
You will need:
1. A valid Pretalx API token
2. An event slug to test against

Press Ctrl+C at any time to cancel.

Enter Pretalx API token (required): *******
Enter event slug [default: pyconde-pydata-2025]:
Enter Pretalx API version [default: v1]: v2

Configuration:
- API Token: Provided ✓
- Event: pyconde-pydata-2025
- API Version: v2

Do you want to proceed with these settings? [Y/n]: Y

Running integration tests...
```

#### Non-Interactive Mode

For automated testing or CI/CD pipelines, you can provide all parameters via command line:

```bash
# Basic usage with token and event
python scripts/run_pretalx_integration_tests.py \
    --token YOUR_TOKEN \
    --event pyconde-pydata-2025

# With specific API version
python scripts/run_pretalx_integration_tests.py \
    --token YOUR_TOKEN \
    --event pyconde-pydata-2025 \
    --api-version v2

# Run specific test only
python scripts/run_pretalx_integration_tests.py \
    --token YOUR_TOKEN \
    --event EVENT \
    --test test_all_endpoints

# Quiet mode (less verbose)
python scripts/run_pretalx_integration_tests.py \
    --token YOUR_TOKEN \
    --event EVENT \
    --quiet
```

### Understanding Test Output

The integration test will:

1. First validate your authentication token and event slug
2. Display detailed API calls including URLs and headers
3. Test each Pretalx endpoint systematically
4. Show real-time results for each endpoint:
   - ✓ Success with item count for list endpoints
   - ✗ Failure with error details
5. Test backward compatibility features
6. Provide a summary with success rate

Example output:
```
================================================================================
VALIDATING TEST CONFIGURATION
================================================================================

Configuration:
  API Version: v2
  API Token: Provided
  Event Slug: pyconde-pydata-2025

1. Testing authentication token...

🌐 API Call:
   URL: https://pretalx.com/api/me
   Headers: {'Pretalx-Version': 'v2', 'Authorization': 'Token 12345678...'}
   Response: 200 OK
   ✓ Authentication successful! Logged in as: John Doe (john@example.com)

2. Validating event 'pyconde-pydata-2025'...

🌐 API Call:
   URL: https://pretalx.com/api/events/pyconde-pydata-2025/
   Headers: {'Pretalx-Version': 'v2', 'Authorization': 'Token 12345678...'}
   Response: 200 OK
   ✓ Event found: PyCon DE & PyData 2025
     Date: 2025-04-28 to 2025-04-30
     Timezone: Europe/Berlin
     Status: Public

✓ All validations passed! Proceeding with endpoint tests...
================================================================================

================================================================================
COMPREHENSIVE PRETALX ENDPOINT TEST
Event: pyconde-pydata-2025
API Version: v2
Authenticated: Yes
================================================================================

----------------------------------------
Testing EVENT endpoints...
----------------------------------------

🌐 API Call:
   URL: https://pretalx.com/api/events/?limit=5
   Headers: {'Pretalx-Version': 'v2', 'Authorization': 'Token 12345678...'}
   Response: 200 OK
✓ /api/events/: SUCCESS (found 5 items)

[... more endpoints with API call details ...]

================================================================================
TEST SUMMARY
================================================================================

Endpoints Tested: 25
✓ Successful: 23
✗ Failed: 2

Failed endpoints:
  - /api/events/pyconde-pydata-2025/reviews/: HTTP 403
  - /api/events/pyconde-pydata-2025/reviews/1/: HTTP 403

Test Environment:
  API Version: v2
  Event: pyconde-pydata-2025
  Authentication: Yes

Success rate: 92.0%
```

### Interpreting Results

- **Success Rate**: A success rate of 70% or higher is considered passing. Some endpoints may require special permissions.
- **Expected Failures**:
  - 401/403 errors for protected endpoints without proper permissions
  - 404 errors for endpoints that don't exist in your Pretalx instance
- **Backward Compatibility**: Tests verify that ID references are properly expanded to full objects

### Using Environment Variables

You can also set environment variables instead of using command-line arguments:

```bash
export PRETALX_API_TOKEN="your-token"
export PRETALX_TEST_EVENT="pyconde-pydata-2025"
export PRETALX_API_VERSION="v2"

python scripts/run_pretalx_integration_tests.py
```

### Using Hatch for Development

If you're contributing to Pytanis, you can use Hatch to run integration tests in a properly configured environment:

```bash
# Run integration tests interactively
hatch run integration

# Run with arguments
hatch run integration --token YOUR_TOKEN --event pyconde-pydata-2025

# Quick run with environment variables
export PRETALX_API_TOKEN="your-token"
export PRETALX_TEST_EVENT="pyconde-pydata-2025"
hatch run integration-quick

# Run pytest directly with more control
hatch run test-endpoints

# Run specific test
hatch run test-endpoints -k test_all_endpoints

# Enter hatch shell for multiple commands
hatch shell
python scripts/run_pretalx_integration_tests.py
```

### Direct pytest Usage

For more control, you can run the tests directly with pytest:

```bash
# Set environment variables first
export PRETALX_API_TOKEN="your-token"
export PRETALX_TEST_EVENT="pyconde-pydata-2025"
export PRETALX_API_VERSION="v2"

# Run all integration tests
pytest tests/pretalx/test_all_endpoints_integration.py -v -s

# Run with specific markers
pytest -m integration -v -s
```

### Troubleshooting

**"API token is required" error**
- Integration tests require a valid API token to test all endpoints properly
- Obtain a token from your Pretalx account settings

**Timeout errors**
- The Pretalx API can be slow, especially for large events
- Consider testing with a smaller event first
- Use the `--test` option to run specific tests

**High failure rate**
- Check your API token has the necessary permissions
- Verify the event slug exists and is accessible
- Some endpoints may not be available in your Pretalx instance

**SSL/Certificate errors**
- Ensure your system certificates are up to date
- Check if you're behind a corporate proxy

### Best Practices

1. **Regular Testing**: Run integration tests before upgrading Pytanis or when you suspect API changes
2. **Event Selection**: Use a test event with moderate data for faster testing
3. **API Version**: Always test with the API version you plan to use in production
4. **Token Security**: Never commit your API token to version control
5. **CI/CD Integration**: Include integration tests in your deployment pipeline with proper secret management

## Unit Tests

To run the standard unit tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pytanis

# Run specific test file
pytest tests/pretalx/test_models.py
```

For more information about testing, see the [development guide](../contributing.md).

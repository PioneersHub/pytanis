# Integration Test Review Against OpenAPI Schema

## Summary

After reviewing the OpenAPI schema at `src/pytanis/pretalx/schema.yml` and comparing it with our integration tests in `test_all_endpoints_integration.py`, here are the key findings:

## Current Test Coverage

### ✅ Well-Tested Endpoints (18 endpoints)
- **Core**: `/api/me/`, `/api/events/`, `/api/events/{event}/`
- **Submissions**: List and detail endpoints
- **Speakers**: List and detail endpoints
- **Talks**: List and detail endpoints (custom implementation with fallback)
- **Reviews**: List and detail endpoints (auth-required)
- **Rooms**: List and detail endpoints
- **Questions**: List and detail endpoints
- **Answers**: List and detail endpoints (auth-required)
- **Tags**: List and detail endpoints

### ❌ Missing from Tests (30 endpoints)
- **Access Codes** (5 endpoints) - for speaker/reviewer access management
- **Schedules** (5 endpoints) - critical for conference schedule management
- **Slots** (3 endpoints) - individual schedule slots
- **Submission Actions** (8 endpoints) - accept/reject/confirm/cancel submissions
- **Submission Types** (2 endpoints) - used internally but not tested directly
- **Tracks** (2 endpoints) - used internally but not tested directly
- **Mail Templates** (2 endpoints) - email template management
- **Teams/Organisation** (5 endpoints) - team management
- **Others**: Upload, Question Options, Speaker Information

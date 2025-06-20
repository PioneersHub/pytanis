# Changelog for v0.9.0

## New Features

### Pretalx API Updates
- Event model: `urls` field is now optional (was required) to support new API structure
- Updated to support new Pretalx API structure where IDs replace nested objects
- Implemented transparent backward compatibility layer

### Cache Optimization
- Added automatic cache pre-population for bulk operations
- New methods: `submission_types()`, `submission_type()`, `tracks()`, `track()`
- Added cache management: `set_cache_prepopulation()`, `clear_caches()`
- Reduces API calls from 200-300 to ~4 for typical queries

### Integration Testing
- Comprehensive integration test suite for all Pretalx endpoints
- Interactive CLI for running integration tests
- API coverage analysis (37.5% of endpoints tested)
- Support for configurable API versions

### Storage Abstraction (from 0.8.0)
- New abstraction layer for storage providers
- Support for local files (CSV/Excel) and Google Sheets
- Optional dependencies for Google, HelpDesk, and Mailgun

## Improvements
- Better error handling for missing API endpoints
- Verbose logging option for debugging API calls
- Session-only caching (not persisted)
- Smart detection of required data for caching

## Bug Fixes
- Fixed circular import in Google storage adapter
- Fixed test compatibility with new API structure
- Handle missing fields gracefully in API responses

## Documentation
- Added comprehensive testing documentation
- API coverage analysis and recommendations
- Integration test usage guide

## Migration Guide

### For most users
No changes required - backward compatibility is maintained.

### For advanced users
- If you were relying on `Event.urls` being required, it's now optional and may be `None`
- Consider using `set_cache_prepopulation(False)` for small queries to avoid bulk fetching
- New integration tests available with `hatch run integration`

### Dependencies
- Pretalx API client is always available (core dependency)
- Optional extras: `pytanis[google]`, `pytanis[helpdesk]`, `pytanis[mailgun]`
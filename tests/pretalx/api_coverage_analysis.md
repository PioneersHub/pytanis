# Pretalx API Coverage Analysis

## Overview
This document compares the endpoints defined in the OpenAPI schema with those tested in our integration tests.

## Endpoints from OpenAPI Schema

### Core Event Endpoints
- ✅ `GET /api/events/` - List all events
- ✅ `GET /api/events/{event}/` - Get specific event details

### Event-specific Endpoints
- ❌ `GET /api/events/{event}/access-codes/` - List access codes
- ❌ `POST /api/events/{event}/access-codes/` - Create access code
- ❌ `GET /api/events/{event}/access-codes/{id}/` - Get access code
- ❌ `PATCH /api/events/{event}/access-codes/{id}/` - Update access code
- ❌ `DELETE /api/events/{event}/access-codes/{id}/` - Delete access code

- ✅ `GET /api/events/{event}/answers/` - List answers (requires auth)
- ✅ `GET /api/events/{event}/answers/{id}/` - Get answer (requires auth)

- ❌ `GET /api/events/{event}/mail-templates/` - List mail templates
- ❌ `GET /api/events/{event}/mail-templates/{id}/` - Get mail template

- ❌ `GET /api/events/{event}/question-options/` - List question options
- ❌ `GET /api/events/{event}/question-options/{id}/` - Get question option

- ✅ `GET /api/events/{event}/questions/` - List questions
- ✅ `GET /api/events/{event}/questions/{id}/` - Get question

- ✅ `GET /api/events/{event}/reviews/` - List reviews (requires auth)
- ✅ `GET /api/events/{event}/reviews/{id}/` - Get review (requires auth)

- ✅ `GET /api/events/{event}/rooms/` - List rooms
- ✅ `GET /api/events/{event}/rooms/{id}/` - Get room

- ❌ `GET /api/events/{event}/schedules/` - List schedules
- ❌ `GET /api/events/{event}/schedules/by-version/` - Get schedule by version
- ❌ `POST /api/events/{event}/schedules/release/` - Release schedule
- ❌ `GET /api/events/{event}/schedules/{id}/` - Get schedule
- ❌ `GET /api/events/{event}/schedules/{id}/exporters/{name}/` - Export schedule

- ❌ `GET /api/events/{event}/slots/` - List slots
- ❌ `GET /api/events/{event}/slots/{id}/` - Get slot
- ❌ `GET /api/events/{event}/slots/{id}/ical/` - Get slot iCal

- ❌ `GET /api/events/{event}/speaker-information/` - List speaker information
- ❌ `GET /api/events/{event}/speaker-information/{id}/` - Get speaker information

- ✅ `GET /api/events/{event}/speakers/` - List speakers
- ✅ `GET /api/events/{event}/speakers/{user__code__iexact}/` - Get speaker

- ❌ `GET /api/events/{event}/submission-types/` - List submission types
- ❌ `GET /api/events/{event}/submission-types/{id}/` - Get submission type

- ✅ `GET /api/events/{event}/submissions/` - List submissions
- ❌ `GET /api/events/{event}/submissions/favourites/` - List favourite submissions
- ✅ `GET /api/events/{event}/submissions/{code__iexact}/` - Get submission
- ❌ `POST /api/events/{event}/submissions/{code__iexact}/accept/` - Accept submission
- ❌ `POST /api/events/{event}/submissions/{code__iexact}/add-speaker/` - Add speaker
- ❌ `POST /api/events/{event}/submissions/{code__iexact}/cancel/` - Cancel submission
- ❌ `POST /api/events/{event}/submissions/{code__iexact}/confirm/` - Confirm submission
- ❌ `POST /api/events/{event}/submissions/{code__iexact}/make-submitted/` - Mark as submitted
- ❌ `POST /api/events/{event}/submissions/{code__iexact}/reject/` - Reject submission
- ❌ `POST /api/events/{event}/submissions/{code__iexact}/remove-speaker/` - Remove speaker
- ❌ `POST /api/events/{event}/submissions/{code}/favourite/` - Toggle favourite

- ✅ `GET /api/events/{event}/tags/` - List tags
- ✅ `GET /api/events/{event}/tags/{id}/` - Get tag (Note: we use tag name, not ID)

- ❌ `GET /api/events/{event}/tracks/` - List tracks
- ❌ `GET /api/events/{event}/tracks/{id}/` - Get track

### Organisation Endpoints
- ❌ `GET /api/organisers/{organiser}/teams/` - List teams
- ❌ `GET /api/organisers/{organiser}/teams/{id}/` - Get team
- ❌ `POST /api/organisers/{organiser}/teams/{id}/invite/` - Invite to team
- ❌ `GET /api/organisers/{organiser}/teams/{id}/invites/{invite_id}/` - Get invite
- ❌ `POST /api/organisers/{organiser}/teams/{id}/remove_member/` - Remove member

### Other Endpoints
- ✅ `GET /api/me/` - Get current user (requires auth)
- ❌ `POST /api/upload/` - Upload file

### Special Endpoints (from client, may use /talks/)
- ✅ `GET /api/events/{event}/talks/` - List talks (may fallback to submissions)
- ✅ `GET /api/events/{event}/talks/{code}/` - Get talk (may fallback to submission)

## Coverage Summary

### Tested Endpoints: 18
- Events: 2/2 ✅
- Submissions: 2/10 (20%)
- Speakers: 2/3 (67%)
- Talks: 2/2 ✅ (custom implementation)
- Reviews: 2/2 ✅
- Rooms: 2/2 ✅
- Questions: 2/2 ✅
- Answers: 2/2 ✅
- Tags: 2/2 ✅
- Me: 1/1 ✅

### Not Tested: 30
- Access Codes: 0/5
- Mail Templates: 0/2
- Question Options: 0/2
- Schedules: 0/5
- Slots: 0/3
- Speaker Information: 0/2
- Submission Types: 0/2
- Submission Actions: 0/8
- Tracks: 0/2
- Teams: 0/5
- Upload: 0/1

### Overall Coverage: 18/48 (37.5%)

## Recommendations

1. **Priority Additions** (commonly used):
   - Submission Types endpoints (needed for backward compatibility)
   - Tracks endpoints (needed for backward compatibility)
   - Schedules endpoints (important for conference planning)
   - Slots endpoints (for schedule details)

2. **Medium Priority**:
   - Access Codes (for speaker/reviewer access)
   - Speaker Information (additional speaker details)
   - Submission action endpoints (accept/reject/confirm)

3. **Low Priority**:
   - Mail Templates (usually managed in UI)
   - Question Options (usually part of questions)
   - Teams (organisational management)
   - Upload (file uploads)

## Missing Client Methods

The following endpoints are in the schema but not implemented in PretalxClient:
- access_codes(), access_code()
- mail_templates(), mail_template()
- question_options(), question_option()
- schedules(), schedule()
- slots(), slot()
- speaker_information()
- submission_types(), submission_type()
- tracks(), track()
- Submission action methods (accept, reject, confirm, etc.)
- Teams-related methods

## Backward Compatibility Notes

Our current implementation fetches submission_types and tracks internally for backward compatibility, but doesn't expose them as public methods. Consider adding:
- `submission_types()` and `submission_type()`
- `tracks()` and `track()`

This would improve API coverage and make the client more complete.
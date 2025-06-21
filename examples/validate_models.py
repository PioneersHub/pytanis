#!/usr/bin/env python3
"""Example script showing how to validate Pretalx models with live data.

This demonstrates using the Pretalx API to fetch data and validate
that all Pydantic models correctly parse the responses.
"""

import os
import sys
from pathlib import Path

import tomli

from pytanis import PretalxClient, get_cfg
from pytanis.config import Config, PretalxCfg
from pytanis.pretalx.models import Event, Speaker, Submission, Talk


def validate_event_data(client: PretalxClient, event_slug: str):
    """Validate Event model with live data."""
    print(f'\nValidating Event model for {event_slug}...')

    try:
        event = client.event(event_slug)
        print(f'✓ Event: {event.name.en or event.name.de or "Unknown"}')
        print(f'  - Date: {event.date_from} to {event.date_to}')
        print(f'  - Locale: {event.locale}')

        # Validate serialization
        event_dict = event.model_dump()
        Event.model_validate(event_dict)
        print('✓ Event model validation successful')

    except Exception as e:
        print(f'✗ Event validation failed: {e}')
        return False

    return True


def validate_submission_data(client: PretalxClient, event_slug: str):
    """Validate Submission models with live data."""
    print('\nValidating Submission models...')

    try:
        count, submissions = client.submissions(
            event_slug, params={'state': 'confirmed', 'limit': 3, 'questions': 'all'}
        )

        print(f'Found {count} submissions, validating first 3...')

        for i, submission in enumerate(submissions):
            print(f'\n  Submission {i + 1}: {submission.title[:50]}...')
            print(f'    - Code: {submission.code}')
            print(f'    - Type: {submission.submission_type.en}')
            print(f'    - Speakers: {len(submission.speakers)}')

            if submission.answers:
                print(f'    - Answers: {len(submission.answers)}')

            # Validate serialization
            sub_dict = submission.model_dump()
            Submission.model_validate(sub_dict)

        print('\n✓ Submission model validation successful')

    except Exception as e:
        print(f'✗ Submission validation failed: {e}')
        return False

    return True


def validate_speaker_data(client: PretalxClient, event_slug: str):
    """Validate Speaker models with live data."""
    print('\nValidating Speaker models...')

    try:
        count, speakers = client.speakers(event_slug, params={'limit': 3})

        print(f'Found {count} speakers, validating first 3...')

        for i, speaker in enumerate(speakers):
            print(f'\n  Speaker {i + 1}: {speaker.name}')
            print(f'    - Code: {speaker.code}')
            print(f'    - Submissions: {len(speaker.submissions)}')

            # Validate serialization
            speaker_dict = speaker.model_dump()
            Speaker.model_validate(speaker_dict)

        print('\n✓ Speaker model validation successful')

    except Exception as e:
        print(f'✗ Speaker validation failed: {e}')
        return False

    return True


def validate_talk_data(client: PretalxClient, event_slug: str):
    """Validate Talk models with live data."""
    print('\nValidating Talk models...')

    try:
        count, talks = client.talks(event_slug, params={'limit': 3})

        print(f'Found {count} talks, validating first 3...')

        for i, talk in enumerate(talks):
            print(f'\n  Talk {i + 1}: {talk.title[:50]}...')
            print(f'    - Code: {talk.code}')

            if talk.slot:
                print(f'    - Scheduled: {talk.slot.start}')
                if talk.slot.room:
                    print(f'    - Room ID: {talk.slot.room}')

            # Validate serialization
            talk_dict = talk.model_dump()
            Talk.model_validate(talk_dict)

        print('\n✓ Talk model validation successful')

    except Exception as e:
        print(f'✗ Talk validation failed: {e}')
        return False

    return True


def main():
    """Main function to run model validations."""
    # Check if we have an API token
    if not os.getenv('PRETALX_API_TOKEN'):
        print('Note: PRETALX_API_TOKEN not set. Using config file.')

        try:
            # Try to use existing config
            config = get_cfg()
            if not config.Pretalx.api_token:
                print('Error: No API token found in config file either.')
                print('Please set PRETALX_API_TOKEN or configure ~/.pytanis/config.toml')
                sys.exit(1)
        except Exception as e:
            print(f'Error loading config: {e}')
            print('Please set PRETALX_API_TOKEN environment variable')
            sys.exit(1)

        client = PretalxClient(config)
    else:
        # Create client with token from environment
        config = Config(
            cfg_path=Path.home() / '.pytanis' / 'config.toml',
            Pretalx=PretalxCfg(api_token=os.getenv('PRETALX_API_TOKEN')),
        )
        client = PretalxClient(config)

    # Get event slug from environment or use default
    test_config_path = Path(__file__).parent.parent / 'test_config.toml'
    if test_config_path.exists():
        with open(test_config_path, 'rb') as f:
            test_config = tomli.load(f)
            default_event_slug = test_config.get('test', {}).get('event_slug')

    event_slug = os.getenv('PRETALX_TEST_EVENT', default_event_slug)

    print(f'Validating Pretalx models for event: {event_slug}')
    print('=' * 60)

    # Run validations
    all_valid = True
    all_valid &= validate_event_data(client, event_slug)
    all_valid &= validate_submission_data(client, event_slug)
    all_valid &= validate_speaker_data(client, event_slug)
    all_valid &= validate_talk_data(client, event_slug)

    print('\n' + '=' * 60)
    if all_valid:
        print('✓ All model validations passed!')
    else:
        print('✗ Some validations failed.')
        sys.exit(1)


if __name__ == '__main__':
    main()

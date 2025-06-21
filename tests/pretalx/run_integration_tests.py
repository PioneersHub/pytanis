#!/usr/bin/env python3
"""Interactive CLI for running Pretalx integration tests.

This script provides an interactive way to run the comprehensive integration tests,
prompting for API token and event slug with proper validation.

Usage:
    # Interactive mode
    python tests/pretalx/run_integration_tests.py

    # Non-interactive mode
    python tests/pretalx/run_integration_tests.py --token YOUR_TOKEN --event EVENT_SLUG

    # Show help
    python tests/pretalx/run_integration_tests.py --help
"""

import argparse
import getpass
import os
import subprocess  # noqa: S404
import sys


def print_banner():
    """Print a welcome banner."""
    print('=' * 60)
    print('Pretalx Integration Test Runner')
    print('=' * 60)
    print()
    print('This tool will run comprehensive integration tests against the Pretalx API.')
    print('You will need:')
    print('1. A valid Pretalx API token')
    print('2. An event slug to test against')
    print()
    print('Press Ctrl+C at any time to cancel.')
    print()


def get_api_token(args):
    """Get API token from args or prompt user."""
    if args.token:
        return args.token

    try:
        token = getpass.getpass('Enter Pretalx API token (required): ')
        return token.strip() if token else None
    except KeyboardInterrupt:
        print('\nCancelled.')
        sys.exit(1)


def get_event_slug(args):
    """Get event slug from args or prompt user."""
    if args.event:
        return args.event

    default_event = 'pyconde-pydata-2025'
    try:
        event = input(f'Enter event slug [default: {default_event}]: ').strip()
        return event if event else default_event
    except KeyboardInterrupt:
        print('\nCancelled.')
        sys.exit(1)


def get_api_version(args):
    """Get API version from args or prompt user."""
    if args.api_version:
        return args.api_version

    default_version = 'v1'
    try:
        version = input(f'Enter Pretalx API version [default: {default_version}]: ').strip()
        return version if version else default_version
    except KeyboardInterrupt:
        print('\nCancelled.')
        sys.exit(1)


def confirm_settings(token, event, api_version):
    """Ask user to confirm the settings."""
    print()
    print('Configuration:')
    print(f'- API Token: {"Provided ✓" if token else "Not provided (limited coverage)"}')
    print(f'- Event: {event}')
    print(f'- API Version: {api_version}')
    print()

    try:
        response = input('Do you want to proceed with these settings? [Y/n]: ').strip().lower()
        return response in {'', 'y', 'yes'}
    except KeyboardInterrupt:
        print('\nCancelled.')
        sys.exit(1)


def run_tests(token, event, api_version, verbose=True, specific_test=None):
    """Run the integration tests with the provided settings."""
    # Set environment variables
    env = os.environ.copy()
    if token:
        env['PRETALX_API_TOKEN'] = token
    env['PRETALX_TEST_EVENT'] = event
    env['PRETALX_API_VERSION'] = api_version

    # Build pytest command
    cmd = [sys.executable, '-m', 'pytest']

    # Add the test file or specific test
    if specific_test:
        cmd.append(f'tests/pretalx/test_all_endpoints_integration.py::{specific_test}')
    else:
        cmd.append('tests/pretalx/test_all_endpoints_integration.py')

    # Add verbose and show output flags
    if verbose:
        cmd.extend(['-v', '-s'])

    # Add color
    cmd.append('--color=yes')

    # Show what we're running
    print()
    print('Running integration tests...')
    print(f'Command: {" ".join(cmd)}')
    print()

    # Run the tests
    try:
        result = subprocess.run(cmd, env=env, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print('\n\nTest run cancelled.')
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run Pretalx integration tests interactively or with command-line arguments.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended for first-time use)
  %(prog)s
  
  # Non-interactive mode with token and event
  %(prog)s --token YOUR_TOKEN --event pyconde-pydata-2025
  
  # Run specific test
  %(prog)s --token YOUR_TOKEN --event EVENT --test test_all_endpoints
""",
    )

    parser.add_argument('--token', '-t', help='Pretalx API token (will prompt if not provided)')
    parser.add_argument('--event', '-e', help='Event slug to test against (will prompt if not provided)')
    parser.add_argument('--api-version', '-v', help='Pretalx API version to use (default: v1)')
    parser.add_argument('--test', help='Run specific test method (e.g., test_all_endpoints)')
    parser.add_argument('--quiet', '-q', action='store_true', help='Less verbose output')

    args = parser.parse_args()

    # Interactive mode if not all required args provided
    interactive = not (args.event and args.token)

    if interactive:
        print_banner()

    # Get token
    token = get_api_token(args)

    # Get event
    event = get_event_slug(args)

    # Get API version
    api_version = get_api_version(args)

    # Validate inputs
    if not event:
        print('\nError: Event slug is required!')
        sys.exit(1)

    if not token:
        print('\nError: API token is required for integration tests!')
        print('Please provide a valid Pretalx API token to test all endpoints.')
        sys.exit(1)

    # In non-interactive mode, proceed directly
    if not interactive:
        return run_tests(token, event, api_version, verbose=not args.quiet, specific_test=args.test)

    # In interactive mode, confirm settings
    if not confirm_settings(token, event, api_version):
        print('Cancelled.')
        sys.exit(1)

    # Run the tests
    return run_tests(token, event, api_version, verbose=not args.quiet, specific_test=args.test)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\n\nCancelled.')
        sys.exit(1)

#!/usr/bin/env python3
"""
Example script to fetch talks from pretalx and save them as JSON.

This script demonstrates how to use the pytanis library to fetch talks
from pretalx and convert them to a simplified JSON format.

Usage:
    python get_talks.py <event_slug> <output_file> [state]

Example:
    python get_talks.py pycon-2023 talks.json
    python get_talks.py pycon-2023 accepted_talks.json accepted
"""

import sys

from pytanis import PretalxClient, save_talks_to_json


def main():
    """Main function to fetch talks and save them as JSON."""
    min_args = 3
    if len(sys.argv) < min_args:
        print(f'Usage: {sys.argv[0]} <event_slug> <output_file> [state]')
        sys.exit(1)

    event_slug = sys.argv[1]
    output_file = sys.argv[2]
    state_value = sys.argv[3] if len(sys.argv) > min_args else 'confirmed'

    # Initialize the pretalx client
    pretalx_client = PretalxClient()

    # Save talks to JSON with enhanced information
    # This will include title, speakers, organisation, track, domain/python expertise levels,
    # duration, abstract, description, and prerequisites
    print(f'Fetching {state_value} talks for event: {event_slug}')
    save_talks_to_json(pretalx_client, event_slug, output_file, state_value)
    print(f'Saved {state_value} talks to: {output_file}')


if __name__ == '__main__':
    main()

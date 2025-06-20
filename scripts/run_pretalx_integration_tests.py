#!/usr/bin/env python3
"""
Convenience script to run Pretalx integration tests.
This simply forwards to the actual test runner in the tests directory.
"""

import subprocess  # noqa: S404
import sys
from pathlib import Path

# Get the path to the actual runner
runner_path = Path(__file__).parent.parent / 'tests' / 'pretalx' / 'run_integration_tests.py'

# Forward all arguments to the actual runner
# Safe because we're only running our own script with user-provided arguments
sys.exit(subprocess.call([sys.executable, str(runner_path)] + sys.argv[1:]))  # noqa: S603

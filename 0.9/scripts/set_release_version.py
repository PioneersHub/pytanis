"""Generate and sets the PYTANIS_VERSION environment variable

Copyright (c) 2017, Ofek Lev, MIT License

Taken from: https://github.com/pypa/hatch/blob/master/scripts/set_release_version.py
"""

import os

from packaging.version import Version

from pytanis import __version__


def main():
    version = Version(__version__)
    with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as f:
        f.write(f'PYTANIS_VERSION={version.major}.{version.minor}\n')


if __name__ == '__main__':
    main()

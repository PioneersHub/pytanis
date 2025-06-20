<div align="center">

<img src="https://raw.githubusercontent.com/pioneershub/pytanis/main/docs/assets/images/logo.svg" alt="Pytanis logo" width="500" role="img">
</div>

Pytanis includes a [Pretalx] client and all the tooling you need for conferences using [Pretalx], from handling the initial call for papers to creating the final program.
<br/>

|         |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CI/CD   | [![CI - Test](https://github.com/pioneershub/pytanis/actions/workflows/run-tests.yml/badge.svg)](https://github.com/pioneershub/pytanis/actions/workflows/run-tests.yml) [![Coverage](https://img.shields.io/coveralls/github/PioneersHub/pytanis/main.svg?logo=coveralls&label=Coverage)](https://coveralls.io/github/PioneersHub/pytanis) [![CD - Build](https://github.com/pioneershub/pytanis/actions/workflows/publish-pkg.yml/badge.svg)](https://github.com/pioneershub/pytanis/actions/workflows/publish-pkg.yml) [![Docs - Build](https://github.com/pioneershub/pytanis/actions/workflows/build-rel-docs.yml/badge.svg)](https://github.com/pioneershub/pytanis/actions/workflows/build-rel-docs.yml)                                                                                                            |
| Package | [![PyPI - Version](https://img.shields.io/pypi/v/pytanis.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/pytanis/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/pytanis.svg?color=blue&label=Downloads&logo=pypi&logoColor=gold)](https://pypistats.org/packages/pytanis) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytanis.svg?logo=python&label=Python&logoColor=gold)](https://pypi.org/project/pytanis/)                                                                                                                                                                                                                                                                                                                                                                                        |
| Details | [![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch) [![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff) [![types - Mypy](https://img.shields.io/badge/Types-Mypy-blue.svg)](https://github.com/python/mypy) [![License - MIT](https://img.shields.io/badge/License-MIT-9400d3.svg)](https://spdx.org/licenses/) [![GitHub Sponsors](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=ff69b4)](https://github.com/sponsors/pioneershub) |

**Trivia**: The name *Pytanis* is a reference to [Prytanis] using the typical *py* prefix of [Python] tools. [Prytanis]
was the name given  to the leading members of the government of a city (polis) in ancient Greece. Offices that used this
title usually had responsibility for presiding over councils of some kind, which met in the [Prytaneion]. Romani ite domum!

## Features

- [x] simple configuration management with a config folder in your home directory, just like many other tools do
- [x] easily access [Google Sheets], potentially filled by some [Google Forms], and download sheets as data frames
- [x] easy to use [Pretalx] client that returns proper Python objects thanks to the power of [pydantic]
- [x] simple e-mail clients for batch mails, e.g. to your reviewers, via [Mailgun] and [HelpDesk]
- [x] awesome [documentation] with best practices for the program committee of any community-based conference
- [x] tools to assign proposals to reviewers based on constraints like preferences
- [x] tools to support the final selection process of proposals
- [x] tools to support the creation of the final program schedule

## Getting started

To install Pytanis simple run:

```commandline
pip install pytanis
```

or to install all recommended additional dependencies:

```commandline
pip install 'pytanis[all]'
```

Then create a configuration file and directory in your user's home directory. For Linux/MacOS/Unix use
`~/.pytanis/config.toml` and for Windows `$HOME\.pytanis\config.toml`, where `$HOME` is e.g. `C:\Users\yourusername\`.
Use your favourite editor to open `config.toml` within the `.pytanis` directory and add the following content:

```toml
[Pretalx]
api_token = "932ndsf9uk32nf9sdkn3454532nj32jn"

[Google]
client_secret_json = "client_secret.json"
token_json = "token.json"
service_user_authentication = false

[HelpDesk]
account = "934jcjkdf-39df-9df-93kf-934jfhuuij39fd"
entity_id = "email@host.com"
token = "dal:Sx4id934C3Y-X934jldjdfjk"

[Mailgun]
token = "gguzdgshbdhjsb87239njsa"
from_address = "PyCon DE & PyData Program Committee <program25@mg.pycon.de>"
reply_to = "program25@pycon.de"
```

where you need to replace the dummy values in the sections `[Pretalx]` and `[HelpDesk]` accordingly. Note that `service_user_authentication` is not required to be set if authentication via a service user is not necessary (see [GSpread using Service Account] for more details).

### Retrieving the Credentials and Tokens

- **Google**:
  - For end users: Follow the [Python Quickstart for the Google API] to generate and download the file `client_secret.json`.
Move it to the `~/.pytanis` folder as `client_secret.json`. The file `token.json` will be automatically generated
later. Note that `config.toml` references those two files relative to its own location.
  - For any automation project: Follow [GSpread using Service Account] to generate and download the file `client_secret.json`.
Move it to the `~/.pytanis` folder as `client_secret.json`. Also make sure to set `service_user_authentication = true` in your `~/.pytanis/config.toml`.
- **Pretalx**: The API token can be found in the [Pretalx user settings].
- **HelpDesk**: Login to the [LiveChat Developer Console] then go to <kbd>Tools</kbd> » <kbd>Personal Access Tokens</kbd>.
  Choose <kbd>Create new token +</kbd>, enter a the name `Pytanis`, select all scopes and confirm. In the following screen
  copy the `Account ID`, `Entity ID` and `Token` and paste them into `config.toml`.
  In case there is any trouble with livechat, contact a helpdesk admin. Also note that the `Account ID` from your token is
  the `Agent ID` needed when you create a ticket. The `Team ID` you get from [HelpDesk] then <kbd>Agents</kbd> »
  <kbd>Name of your agent</kbd> and the final part of the URL shown now.

  **When setting up your agent the first time**,
  you also need to go to [LiveChat] then log in with your Helpdesk team credentials and click <kbd>Request</kbd> to get an invitation.
  An admin of [LiveChat] needs to confirm this and add you as role `admin`. Then, check [HelpDesk] to receive the invitation
  and accept.

## Development

This section is only relevant if you want to contribute to Pytanis itself. Your help is highly appreciated! There are two options for local development.

Whilst both option are valid, the Devcontainer setup is the most convenient, as all dependencies are preconfigured.

### Devcontainer Setup

After having cloned this repository:

1. Make sure to have a local installation of [Docker] and [VS Code] running.
2. Open [VS Code] and make sure to have the [Dev Containers Extension] from Microsoft installed.
3. Open the cloned project in [VS Code] and from the bottom right corner confirm to open the project to be opened within the Devcontainer.

If you miss any dependencies check out the `devcontainer.json` within the `.devcontainer` folder. Otherwise, the right python environment with [pipx], [hatch], [pre-commit] and the initialization steps for the Hatch environments, are already included.

For the use of the `pytanis` libary some credentials and tokens are necessary (see the "Getting Started" section). With the Devcontainer setup the `config.yaml` is already created. Just navigate to `~/.pytanis/config.toml` and update the file with the corresponding tokens.

### Conventional Setup

After having cloned this repository:

1. install [hatch] globally, e.g. `pipx install hatch`,
2. install [pre-commit] globally, e.g. `pipx install pre-commit`,
3. \[only once\] run `hatch config set dirs.env.virtual .direnv`  to let [VS Code] find your virtual environments.


And then you are already set up to start hacking. Use `hatch run` to do everything you would normally do in a virtual
environment, e.g. `hatch run jupyter lab` to start [JupyterLab] in the default environment, `hatch run cov` for unit tests
and coverage (like [tox]) or `hatch run docs:serve` to build & serve the documentation. For code hygiene, execute `hatch run lint:all`
in order to run [ruff] and [mypy] or `hatch run lint:fix` to automatically fix formatting issues.
Check out the `[tool.hatch.envs]` sections  in [pyproject.toml](pyproject.toml) to learn about other commands.
If you really must enter a virtual environment, use `hatch shell` to enter the default environment.

## Testing

### Integration Tests

Pytanis includes comprehensive integration tests to validate compatibility with the Pretalx API. These tests ensure all data models work correctly with live API responses.

To run integration tests interactively:

```shell
# Using Hatch (recommended for development)
hatch run integration

# Or directly
python scripts/run_pretalx_integration_tests.py
```

This will prompt you for:
- Pretalx API token (required)
- Event slug to test against
- API version to use

For automated testing:

```shell
# Using Hatch with arguments
hatch run integration --token YOUR_TOKEN --event pyconde-pydata-2025

# Using environment variables for quick testing
export PRETALX_API_TOKEN="your-token"
export PRETALX_TEST_EVENT="pyconde-pydata-2025"
hatch run integration-quick

# Direct pytest for more control
hatch run test-endpoints

# Without Hatch
python scripts/run_pretalx_integration_tests.py --token YOUR_TOKEN --event pyconde-pydata-2025 --api-version v2
```

See [tests/pretalx/README_INTEGRATION.md](tests/pretalx/README_INTEGRATION.md) for more details.

## Documentation

The [documentation] is made with [Material for MkDocs] and is hosted by [GitHub Pages]. Your help to extend the
documentation, especially in the context of using Pytanis for community conferences like [PyConDE], [EuroPython], etc.
is highly appreciated.

## License & Credits

[Pytanis] is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
To start this project off a lot of inspiration and code was taken from [Alexander Hendorf] and [Matthias Hofmann].

[Pytanis]: https://pioneershub.github.io/pytanis/
[Python]: https://www.python.org/
[Pretalx]: https://pretalx.com/
[hatch]: https://hatch.pypa.io/
[pre-commit]: https://pre-commit.com/
[Prytanis]: https://en.wikipedia.org/wiki/Prytaneis
[Prytaneion]: https://en.wikipedia.org/wiki/Prytaneion
[Python Quickstart for the Google API]: https://developers.google.com/sheets/api/quickstart/python
[GSpread using Service Account]: https://docs.gspread.org/en/v5.12.4/oauth2.html#for-bots-using-service-account
[Pretalx user settings]: https://pretalx.com/orga/me
[documentation]: https://pioneershub.github.io/pytanis/
[Alexander Hendorf]: https://github.com/alanderex
[Matthias Hofmann]: https://github.com/mj-hofmann
[Google Forms]: https://www.google.com/forms/about/
[Google Sheets]: https://www.google.com/sheets/about/
[pydantic]: https://docs.pydantic.dev/
[HelpDesk]: https://www.helpdesk.com/
[Material for MkDocs]: https://github.com/squidfunk/mkdocs-material
[GitHub Pages]: https://docs.github.com/en/pages
[PyConDE]: https://pycon.de/
[EuroPython]: https://europython.eu/
[LiveChat Developer Console]: https://platform.text.com/console/
[JupyterLab]: https://jupyter.org/
[tox]: https://tox.wiki/
[mypy]: https://mypy-lang.org/
[ruff]: https://github.com/astral-sh/ruff
[VS Code]: https://code.visualstudio.com/
[LiveChat]: https://www.livechat.com/
[Docker]: https://www.docker.com/
[Dev Containers Extension]: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers
[Mailgun]: https://www.mailgun.com/
[pipx]: https://pipx.pypa.io/

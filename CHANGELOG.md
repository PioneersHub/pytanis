# Changelog

## Version 0.8 (2024-12-30)

- Added support for Mailgun, thanks to Nils Mohr
- Added new notebook for calculating submission statistics, thanks to Nils Mohr
- Added devcontainer for easier development, thanks to Nils Mohr
- Updated all dependencies, added support for Python 3.13
- Added configurable Pretalx API version support via `api_version` config parameter (defaults to "v1")

## Version 0.7.2 (2024-06-18)

- Matplotlib replaced with webcolors, thanks Alexander Hendorf
- Updated ruff, pre-commit, mypy etc.

## Version 0.7.1 (2024-01-29)

- Pin gspread to <6.0 because API was broken

## Version 0.7 (2024-01-01)

- Switched for reproducability to [hatch-pip-compile](https://github.com/juftin/hatch-pip-compile)
- A few fixes to make mypy happy
- Some more pydantic v2 deprecations migrated to new API
- Renamed `GSheetClient` to `GSheetsClient`
- Added Gspread service user authentication

## Version 0.6.1 (2023-12-10)

- Fixed a deadlock problem in `utils.throttle`

## Version 0.6 (2023-12-04)

- Migrate to Pydantic v2
- Require mininum Python version of 3.10

## Version 0.5 (2023-04-10)

- Change the start/end time of a slot to a datetime

## Version 0.4.1 (2023-03-25)

- Additional documentation about the CfP and some minor fixes

## Version 0.4 (2023-03-10)

- More functionality regarding the proposal selection process like `mark_rows`
- Pretalx submissions states are now proper Enums.
- `GSheetClient.save_df_as_gsheet` also applies some default `BasicFormatter` for nicer headlines etc.
- Added some MIP helpers (`highs`) to support the scheduling process
- Extended the documentation quite a bit

## Version 0.3 (2023-02-17)

- Allow creating a worksheet from `GSheetClient`
- Make `get_cfg` importable from `pytanis`
- Fix bug in `PretalxClient` that returned wrong number of results if a list was passed as `params` in conjunction with
  pagination.

## Version 0.2 (2023-02-11)

- have a progress bar for long-running commands when possible
- switched to [gspread](https://docs.gspread.org/) for handling the low-level GoogleAPI
- using [gspread-dataframe](https://gspread-dataframe.readthedocs.io/) for converting a worksheet into a dataframe
- timeout of 60s for PretalxAPI as it is really slow, which caused a lot of timeout errors
- rename `*API` to `*Client` as it's rather a client for an API
- moved some functionality from `review` to `pretalx.utils`
- `GSheetClient` allows now uploading dataframes as Google Sheets
- an awesome logo created by Paula González Avalos
- way more usage documentation

## Version 0.1.1 (2023-01-16)

- fix typo `sent` -> `send` in MailClient

## Version 0.1 (2023-01-15)

- First alpha version that can be used
- Google client to retrieve Google Sheets implemented
- Pretalx client implement
- A very basic HelpDesk client (minimal functionality) implemented
- Basic e-mail client implemented to send mails via HelpDesk
- Central configuration management for secrets and credentials implemented

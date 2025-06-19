## Installation

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
api_version = "v1"  # Optional, defaults to "v1" if not specified

[Google]
client_secret_json = "client_secret.json"
token_json = "token.json"

[HelpDesk]
account = "934jcjkdf-39df-9df-93kf-934jfhuuij39fd"
entity_id = "email@host.com"
token = "dal:Sx4id934C3Y-X934jldjdfjk"
```
where you need to replace the dummy values in the sections `[Pretalx]` and `[HelpDesk]` accordingly.

!!! info
    You have to configure the credentials and tokens only for the sections you actually want to use.
    For instance, `[Pretalx]` and `[Google]` are the most important sections for users that want to interact with
    [Pretalx] and also [Google Sheets]. If for instance no access to [HelpDesk] is necessary, e.g. no
    mails need to be sent, you can just leave out the key/value pairs in the `[HelpDesk]` section.


## Retrieving the Credentials and Tokens
* **Google**: Follow the [Python Quickstart for the Google API] to generate and download the file `client_secret.json`.
Move it to the `~/.pytanis` folder as `client_secret.json`. The file `token.json` will be automatically generated
later. Note that `config.toml` references those two files relative to its own location.
* **Pretalx**: The API token can be found in the [Pretalx user settings].
* **HelpDesk**: Log into the [LiveChat Developer Console] then go to <kbd>Tools</kbd> » <kbd>Personal Access Tokens</kbd>.
  Hit <kbd>Create new token +</kbd>, enter a the name `Pytanis`, select all scopes and confirm. In the following screen
  copy the `Account ID`, `Entity ID` and `Token` and paste them into `config.toml`.
  In case there is any trouble with livechat, contact a helpdesk admin.

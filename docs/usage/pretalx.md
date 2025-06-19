## Basic Usage

Pytanis offers easy access to the [Pretalx API] and the usage is quite self-explanatory. Let's look at some basic
example:
```python
from pytanis import PretalxClient

event_name = "pyconde-pydata-berlin-2023"

pretalx_client = PretalxClient()
subs_count, subs = pretalx_client.submissions(event_name)
```
This simple code will return the total number of submissions as `subs_count` and an iterator of all submissions `subs`.
When iterating over `subs` new requests will be made internally to the Pretalx server to retrieve more result pages. This
method of retrieving partial results is called *pagination*. Quite often you will just use `subs = list(subs)` to retrieve
all submissions and get a list instead for easier handling. If you want to retrieve always all results directly,
i.e. in a blocking way, you can tell this to the client via `PretalxClient(blocking=True)` but be aware that you must still
call `subs = list(subs)`.

All endpoints of the [Pretalx API] are implemented in Pytanis and the method name corresponds to the name of the endpoint.
Additional parameters can be passed using the `params` argument like e.g.:
```python
subs_count, subs = pretalx_client.submissions(
    event_name, params={"questions": "all", "state": "submitted"}
)
```
Check the [Pretalx API] for a list of options.

## API Version Configuration

Pytanis supports configuring the Pretalx API version through the configuration file. By default, it uses API version "v1", but you can change this if needed:

```toml
[Pretalx]
api_token = "your-api-token"
api_version = "v2"  # Use a different API version
```

The `api_version` setting is optional. If not specified in your `~/.pytanis/config.toml`, it will default to "v1". This version is sent in the `Pretalx-Version` header with each API request.

## Advanced Usage

Find out more about the client's capabilities, e.g. throttling, by looking at Pytanis' reference of the [pretalx client module].

[pretalx client module]: ../../reference/pytanis/helpdesk/client/#pytanis.helpdesk.client

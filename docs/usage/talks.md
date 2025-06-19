# Working with Talks

Pytanis provides functionality to easily extract talks from pretalx and convert them to a simplified JSON format that can be used for various purposes like displaying on websites, creating schedules, etc.

## Basic Usage

The simplest way to get talks as JSON is to use the `get_talks_as_json` function:

```python
from pytanis import PretalxClient, get_talks_as_json

# Initialize the pretalx client
pretalx_client = PretalxClient()

# Get JSON string with talks (default: confirmed talks)
event_slug = "your-event-slug"
json_data = get_talks_as_json(pretalx_client, event_slug)

# Get JSON string with talks in a different state (e.g., accepted)
json_data = get_talks_as_json(pretalx_client, event_slug, state_value="accepted")

# Print or use the JSON data
print(json_data)
```

## Saving to a File

If you want to save the JSON data to a file, you can use the `save_talks_to_json` function:

```python
from pytanis import PretalxClient, save_talks_to_json

# Initialize the pretalx client
pretalx_client = PretalxClient()

# Save talks to a file (default: confirmed talks)
event_slug = "your-event-slug"
output_file = "talks.json"
save_talks_to_json(pretalx_client, event_slug, output_file)

# Save talks in a different state (e.g., accepted)
save_talks_to_json(pretalx_client, event_slug, "accepted_talks.json", state_value="accepted")
```

## The SimpleTalk Model

The JSON output contains a list of `SimpleTalk` objects with the following structure:

```json
[
  {
    "code": "ABC123",
    "title": "Talk Title",
    "speaker": "Speaker Name 1, Speaker Name 2",
    "organisation": "Company Name",
    "track": "Track Name",
    "domain_level": "Intermediate",
    "python_level": "Advanced",
    "duration": "45",
    "abstract": "Short abstract of the talk",
    "description": "Detailed description of the talk",
    "prerequisites": "Required knowledge or tools"
  },
  ...
]
```

The fields are:

- `code`: The unique code of the talk
- `title`: The title of the talk
- `speaker`: A comma-separated list of speaker names
- `organisation`: The company or institute of the speakers (if available)
- `track`: The track name (if available)
- `domain_level`: The domain expertise level (if available)
- `python_level`: The Python expertise level (if available)
- `duration`: The duration of the talk in minutes
- `abstract`: The abstract of the talk
- `description`: The detailed description of the talk
- `prerequisites`: Any prerequisites for the talk (if available)

## Using the SimpleTalk Model Directly

You can also create `SimpleTalk` objects directly if needed:

```python
from pytanis import SimpleTalk

talk = SimpleTalk(
    code="ABC123",
    title="My Talk",
    speaker="John Doe",
    organisation="Acme Inc.",
    track="Python",
    domain_level="Intermediate",
    python_level="Advanced",
    duration="30",
    abstract="This is a talk about Python",
    description="In this talk, we will explore Python features",
    prerequisites="Basic programming knowledge"
)

# Convert to dict
talk_dict = talk.model_dump()
```

## Example Script

An example script is provided in the `examples` directory:

```bash
# Get confirmed talks
python examples/get_talks.py your-event-slug output.json

# Get talks in a specific state
python examples/get_talks.py your-event-slug output.json accepted
```

This script fetches talks for the specified event and state, and saves them to the specified output file.

## Advanced Usage

If you already have Talk objects and want to convert them to JSON, you can use the `talks_to_json` function:

```python
from pytanis import PretalxClient, talks_to_json

# Initialize the pretalx client
pretalx_client = PretalxClient()

# Fetch talks
event_slug = "your-event-slug"
_, talks = pretalx_client.talks(event_slug, params={"questions": "all"})

# Convert to list to materialize the iterator
talks_list = list(talks)

# Convert to JSON
json_data = talks_to_json(talks_list, pretalx_client, event_slug)
```

## Backward Compatibility

For backward compatibility, the following functions are still available:

- `get_confirmed_talks_as_json`: Alias for `talks_to_json`
- `save_confirmed_talks_to_json`: Similar to `save_talks_to_json` but with a different parameter order

# Working with Confirmed Talks

Pytanis provides functionality to easily extract confirmed talks from pretalx and convert them to a simplified JSON format that can be used for various purposes like displaying on websites, creating schedules, etc.

## Basic Usage

The simplest way to get confirmed talks as JSON is to use the `get_confirmed_talks_as_json` function:

```python
from pytanis import PretalxClient, get_confirmed_talks_as_json

# Initialize the pretalx client
pretalx_client = PretalxClient()

# Fetch all talks with their answers
event_slug = "your-event-slug"
_, talks = pretalx_client.talks(event_slug, params={"questions": "all"})

# Convert to list to materialize the iterator
talks_list = list(talks)

# Get JSON string with confirmed talks
# Pass the pretalx_client and event_slug to fetch speaker data for organisation information
json_data = get_confirmed_talks_as_json(talks_list, pretalx_client, event_slug)

# Print or use the JSON data
print(json_data)
```

## Saving to a File

If you want to save the JSON data to a file, you can use the `save_confirmed_talks_to_json` function:

```python
from pytanis import PretalxClient, save_confirmed_talks_to_json

# Initialize the pretalx client
pretalx_client = PretalxClient()

# Fetch all talks with their answers
event_slug = "your-event-slug"
_, talks = pretalx_client.talks(event_slug, params={"questions": "all"})

# Convert to list to materialize the iterator
talks_list = list(talks)

# Save confirmed talks to a file
# Pass the pretalx_client and event_slug to fetch speaker data for organisation information
output_file = "confirmed_talks.json"
save_confirmed_talks_to_json(talks_list, output_file, pretalx_client, event_slug)
```

## The SimpleTalk Model

The JSON output contains a list of `SimpleTalk` objects with the following structure:

```json
[
  {
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
python examples/get_confirmed_talks.py your-event-slug output.json
```

This script fetches all talks for the specified event, filters for confirmed talks, and saves them to the specified output file.

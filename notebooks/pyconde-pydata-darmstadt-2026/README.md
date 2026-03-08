# Notebooks Instructions
## Write Schedule to Pretalx

To run `notebooks/pyconde-pydata-darmstadt-2026/50_write_schedule_to_pretalx_v1.ipynb`, complete the standard setup in Getting started (Pretalx token + Google credentials). Then additionally:

**1. Launch the notebook environment:**

```bash
hatch run notebook:lab
```

**2. Create the notebook-level `config.toml`** at `notebooks/pyconde-pydata-darmstadt-2026/config.toml`:

```toml
event_name = "pyconde-pydata-darmstadt-2026"
schedule_spread_id = "<Google Sheet ID from the URL>"
schedule_work_name = "<worksheet tab name>"
```

The `schedule_spread_id` is the long ID in the Google Sheet URL: `https://docs.google.com/spreadsheets/d/THIS_PART_HERE/edit`

The tab should have column headers `Day,	Session,	Slot,	Time,	room_name_1, room_name 2, ...`. For instance:
|   Day   | Session |  Slot  |      Time     |                                              Zeiss Plenary (Spectrum) Cap: 100%                                              |                                                   Titanium [2nd Floor] Cap: 23%                                                  |
|:-------:|:-------:|:------:|:-------------:|:----------------------------------------------------------------------------------------------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------------:|
| Tuesday | Morning | First  | 11:45 - 12:10 | talk_title PyCon: talk_topics  talk_duration | talk_title PyCon: talk_topics  talk_duration               |
| Tuesday | Morning | Second | 12:25 - 13:05 | talk_title PyCon: talk_topics  talk_duration Sponsored                                                               | talk_title PyCon: talk_topics  talk_duration |

**3. Update the configuration cell** with the correct conference dates (`CONF_DATES`), timezone (`TIMEZONE`), and room name mappings (`ROOM_MAP`).

**4. Use `DRY_RUN`** — set `DRY_RUN = True` to preview what would be written without touching Pretalx. Set it to `False` to actually write.

**5. Convert the last markdown cell to code** — publish the schedule that has been automatically uploaded to Pretalx.

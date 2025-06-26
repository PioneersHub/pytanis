
## Basic Usage

Pytanis' Google Sheet client is really made for simplicity. Retrieving a worksheet of a Google sheet is as simple as:
```python
from pytanis import GSheetsClient

gsheets_client = GSheetsClient()
gsheet_df = gsheets_client.gsheet_as_df(SPREADSHEET_ID, WORKSHEET_NAME)
```
where `SPREADSHEET_ID` is the ID taken from the spreadsheet's url, e.g. the ID is `17juVXM7V3p7Fgfi-9WkwPlMAYJB-DuxRhYCi_hastbB`
if your spreadsheet's url is `https://docs.google.com/spreadsheets/d/17juVXM7V3p7Fgfi-9WkwPlMAYJB-DuxRhYCi_hastbB/edit#gid=1289752230`,
and `WORKSHEET_NAME` is the name of the actual sheet, e.g. `Form responses 1`, that you find in the lower bar of your
spreadsheet. The function `gsheet_as_df` returns a simple [Pandas] dataframe, which most users are surely familiar with.

If you run the above script the first time, you will get a link to a Google consent page, or it will directly open up if you run
this in a Jupyter notebook. Read it carefully and accept the access to your Google Sheet. This step is only necessary and
everytime you change the access scope. For instance, if you also want to have write-access to a worksheet, run:
```python
gsheets_client = GSheetsClient(read_only=False)
gsheets_client.recreate_token()
```
and you will see the consent screen again, asking this time for write-access. Having accepted, you can now use
```python
gsheets_client.save_df_as_gsheet(subs_df, SPREADSHEET_ID, WORKSHEET_NAME)
```
to upload a dataframe as Google sheet, overriding what's currently in there.

!!! tip
    [Google Sheet] has a real useful version history that can be found under <kbd>File</kbd> » <kbd>Version history</kbd> »
    <kbd>See version history</kbd>. Even if you have accidentally overwritten you Google Sheet you can also restore an old version.


## Advanced Usage

In case you want even more functionality and a dataframe is just not enough, you can use the `gsheet` method to get a
[Worksheet object] or [Spreadsheet object] of [GSpread]. GSpread gives you full access to the API of Google Sheet and
all the `gsheet_as_df` does is to basically use [GSpread-Dataframe] to convert this into a [Pandas] dataframe to simplify
things for you. Also check out [GSpread-Formatting] if you want to use features like conditional formatting, colored cells, etc.
[Pytanis' google module] gives you a complete reference of the current functionality within Pytanis but make sure to check
out the [GSpread] ecosystem too as mentioned above.

[GSpread]: https://docs.gspread.org/
[GSpread-Dataframe]: https://gspread-dataframe.readthedocs.io/
[GSpread-Formatting]: https://gspread-formatting.readthedocs.io/
[Worksheet object]: https://docs.gspread.org/en/latest/api/models/worksheet.html#worksheet
[Spreadsheet object]: https://docs.gspread.org/en/latest/api/models/spreadsheet.html#spreadsheet
[Pytanis' google module]: ../reference/pytanis/google.md#pytanis.google

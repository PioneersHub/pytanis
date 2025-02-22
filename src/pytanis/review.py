"""Tools related to assigning proposals to reviewers

In Pretalx assignments can be done in two directions:

 1. Assign proposals to reviewers
 2. Assign reviewers to proposals

We will always assume direction 1. in this file when we talk about an assignment.
So in Operation Research-speak, resources get assigned tasks, not the other way around.
The time needed for the task of reviewing a proposal is quite homogeneous while the number of reviews a single
reviewer may highly vary. Also, we will rather use the name submission instead of proposal as this also reflects
the naming of the Pretalx API.

We follow the convention over configuration principle here and thus check out the `Col` class for the naming of
columns.
"""

import json
from pathlib import Path

import pandas as pd

from pytanis.pretalx.utils import Col as PretalxCol


class Col(PretalxCol):
    """Additional conventions used for reviews"""

    address_as = 'Address as'
    track_prefs = 'Track Preferences'
    committee_contact = 'Committee Contact'
    committee_member = 'Committee Member'
    all_proposals = 'All Proposals'

    pretalx_activated = 'Pretalx activated'

    curr_assignments = 'Current Assignments'
    nassignments = '#Assignments'

    target_nreviews = 'Target #Reviews'
    rem_nreviews = 'Remaining #Reviews'
    done_nreviews = 'Done #Reviews'

    nvotes = '#Votes'
    vote_score = 'Vote Score'


def read_assignment_as_df(file_path: Path) -> pd.DataFrame:
    """Reads an assignment and returns a dataframe."""
    with open(file_path, encoding='utf8') as fh:
        curr_assign = json.load(fh)
    df = pd.DataFrame({k: [v] for k, v in curr_assign.items()})
    df = df.T.rename_axis(index=Col.email).rename(columns={0: Col.curr_assignments}).reset_index()
    return df


def save_assignments_as_json(df: pd.DataFrame, file_path: Path | str) -> None:
    """Save the dataframe as proposal assignment JSON file.

    We expect `df` to have the columns `Col.email` and `Col.curr_assignments`.
    """
    if df[Col.email].duplicated().any():
        non_unique_mails = df[Col.email][df[Col.email].duplicated(keep=False)].unique().tolist()
        msg = f'Non-unique emails found in the dataframe: {", ".join(non_unique_mails)}'
        raise ValueError(msg)
    file_path = Path(file_path)
    df = df.loc[:, [Col.email, Col.curr_assignments]]
    json_dct = json.loads(df.set_index(Col.email).to_json())[Col.curr_assignments]
    # prettify the json string for human-edit-ability if reviewers need to be dropped later
    json_str = json.dumps(json_dct).replace('{', '{\n').replace('], ', '],\n').replace(']}', ']\n}')
    with open(file_path, 'w', encoding='utf8') as fh:
        fh.write(json_str)

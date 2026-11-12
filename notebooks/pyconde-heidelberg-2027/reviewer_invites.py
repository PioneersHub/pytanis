"""Match the reviewer form against the Pretalx reviewer team.

Plain functions without any API or sheet access, used by 15_invite_reviewers_v1.ipynb.
Run `python reviewer_invites.py` for the self check.
"""

# ruff: noqa: S101, T201  # the self check at the bottom uses assert and print

from typing import Any

# Headers in the form responses tab. WELCOME is spelled like the header in the sheet.
FORM_EMAIL = 'Email address'
WELCOME = 'Recieved welcome mail'
ACTIVATED = 'Activated in Pretalx'
ALL_PROPOSALS = 'All Proposals'
PRETALX_MAIL = 'Pretalx Mail'
PRETALX_NAME = 'Pretalx Name'
PC_COMMENT = 'PC Comment'
EXTRA_COLUMNS = [WELCOME, ACTIVATED, ALL_PROPOSALS, PRETALX_MAIL, PRETALX_NAME, PC_COMMENT]

Row = dict[str, str]
Team = dict[str, Any]


def norm(email: str | None) -> str:
    return (email or '').strip().lower()


def _members_by_email(team: Team) -> dict[str, dict[str, Any]]:
    return {norm(m['email']): m for m in team['members'] if m.get('email')}


def emails_to_invite(rows: list[Row], team: Team) -> list[str]:
    """Form emails that are neither members nor invited yet, once each, in form order.

    Rows with a Pretalx Mail are skipped, as they were matched by hand to an account with another email.
    """
    seen = set(_members_by_email(team)) | {norm(i['email']) for i in team['invites']} | {''}
    to_invite = []
    for row in rows:
        email = norm(row.get(FORM_EMAIL))
        if email not in seen and not norm(row.get(PRETALX_MAIL)):
            seen.add(email)
            to_invite.append(email)
    return to_invite


def cell_updates(rows: list[Row], team: Team) -> list[tuple[int, str, str]]:
    """(position in rows, column, value) for every empty status cell that the team data can fill."""
    members = _members_by_email(team)
    invited = {norm(i['email']) for i in team['invites']} - {''}
    updates = []
    for pos, row in enumerate(rows):
        email = norm(row.get(FORM_EMAIL))
        member = members.get(norm(row.get(PRETALX_MAIL))) or members.get(email)
        if member:
            values = {WELCOME: 'TRUE', ACTIVATED: 'x', PRETALX_MAIL: member['email'], PRETALX_NAME: member['name']}
        elif email in invited:
            values = {WELCOME: 'TRUE'}
        else:
            continue
        updates += [(pos, col, val) for col, val in values.items() if not (row.get(col) or '').strip()]
    return updates


def unmatched_members(rows: list[Row], team: Team) -> list[dict[str, Any]]:
    """Members whose email is in no form row and in no Pretalx Mail cell. These need a match by hand."""
    known = {norm(r.get(FORM_EMAIL)) for r in rows} | {norm(r.get(PRETALX_MAIL)) for r in rows}
    return [m for m in team['members'] if not m.get('email') or norm(m['email']) not in known]


if __name__ == '__main__':
    team = {
        'members': [
            {'code': 'A1', 'email': 'ann@example.com', 'name': 'Ann A'},
            {'code': 'B2', 'email': 'bob.private@example.org', 'name': 'Bob B'},
            {'code': 'C3', 'email': 'cem@example.com', 'name': 'Cem C'},
        ],
        'invites': [{'id': 1, 'email': 'dana@example.com'}],
    }
    rows = [
        {FORM_EMAIL: ' Ann@Example.com ', PRETALX_NAME: 'Ann by hand'},  # member, other case, name typed by hand
        {FORM_EMAIL: 'bob@work.example', PRETALX_MAIL: 'bob.private@example.org'},  # matched by hand
        {FORM_EMAIL: 'dana@example.com'},  # open invite
        {FORM_EMAIL: 'eve@example.com'},  # new
        {FORM_EMAIL: 'EVE@example.com'},  # duplicate of the new one
        {FORM_EMAIL: ''},  # empty row
    ]
    assert emails_to_invite(rows, team) == ['eve@example.com']
    assert cell_updates(rows, team) == [
        (0, WELCOME, 'TRUE'),
        (0, ACTIVATED, 'x'),
        (0, PRETALX_MAIL, 'ann@example.com'),
        (1, WELCOME, 'TRUE'),
        (1, ACTIVATED, 'x'),
        (1, PRETALX_NAME, 'Bob B'),
        (2, WELCOME, 'TRUE'),
    ]
    assert [member['code'] for member in unmatched_members(rows, team)] == ['C3']
    print('reviewer_invites self check passed')

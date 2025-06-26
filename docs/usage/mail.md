## Basic Usage

The usage of Pytanis' mail functionality is really simple. There are only three steps, you instantiate the mail client,
create a mail object with your content and assemble a list of recipients.

### Team & Agent ID

But before we write an e-mail we have to determine the team and agent id so that the e-mails we send are assigned to
the right roles as set up within [HelpDesk]. In order to do this, we can just do:

```python
from pytanis import HelpDeskClient

helpdesk = HelpDeskClient()

print([agent.ID for agent in helpdesk.list_agents() if "AGENTS EMAIL" in agent.email])
print([team.ID for team in helpdesk.list_teams() if "TEAM NAME" in team.name])
```
to find the right IDs with respect to the e-mail address `AGENTS EMAIL` and the corresponding `TEAM NAME`. We assume
now that you stored those two values in `agent_id` and `team_id`, respectively.

### Defining the Recipients

Defining the recipients means that you create a list of [Recipient] objects like:
```python
from pytanis.helpdesk import Recipient

recipients = [
    Recipient(name="Peter Parker", email="peter@parker.com", address_as="Peter"),
    Recipient(name="Mary Watson", email="marry-jane@watson.com", address_as="Mary"),
]
```
in most cases you will create this using a dataframe of some [Google Sheet], and thus it will look more like:
```python
recipients = []
recip_df = google_sheet_df[["First name", "Last name", "E-mail"]]

for _, row in recip_df.iterrows():
    recipient = Recipient(
        name=f"{row['First name']} {row['Last name']}",
        email=row["E-mail"],
        address_as=row["First name"],
    )
    recipients.append(recipient)
```

For more advanced usages, e.g. individual mails corresponding to certain individuals, you can use the `data` parameter of the
`Recipient` that takes a dictionary. Let's say we want to add a special sentence later for Peter to pay his rent, we can define:
```python
Recipient(
    name="Peter Parker",
    email="peter@parker.com",
    address_as="Peter",
    data={"feedback": "Pay your rent, Parker!"},
)
```
In the section, we will see how we can access this special attribute again.

### Writing the E-Mail

So now we can write the actual e-mail text, which just uses the basic string substitution functionality of Python:
```python
mail_body = """
Hi {recipient.address_as}!

This is a message from the Program committee with the subject {mail.subject} :-)
{recipient.data.feedback}

Thank you very much {recipient.address_as} for your support!

All the best,
Program Committee
"""
```
You see that we can use `recipient` and `mail` to access the attributes of the [Recipient] as well as the [Mail] object
to personalize the e-mail.

Now we create the [Mail] object with:
```python
from pytanis.helpdesk import Mail

mail = Mail(
    subject="Deadline is coming soon",
    text=mail_body,
    team_id=team_id,
    agent_id=agent_id,
    status="solved",
    recipients=recipients,
)
```

### Sending an E-mail

Now we have everything assembled to send the e-mail with:
```python
from pytanis.helpdesk import MailClient

mail_client = MailClient()
responses, errors = mail_client.send(mail, dry_run=True)
assert not errors
```
Having `dry_run=True` allows you to test you code and just print the resulting e-mails on your console to check if everything
is like expected. Later set `dry_run=False` to actually send the e-mails via [HelpDesk].

The method `send` returns a list of successful `responses` and a hopefully empty list of `errors`. The `responses` list
is a list of tuples where each tuple holds the [Recipient] as wells as the returned HelpDesk ticket. The `errors` list is
a list of tuples with the [Recipient] and the corresponding exception object which occured when sending the mail to the recipient.

## Advanced Usage

For more details, check out [Pytanis' mail references](../reference/pytanis/helpdesk/mail.md#pytanis.helpdesk.mail)
and also the notebook [20_mail_to_reviewers_v1].


!!! tip
    For contacting your (potential) speakers, [Pretalx] itself has pretty advanced templating and mailing features so
    there is no need to use this functionality here. Just make sure that you refer always to HelpDesk in your mails,
    so that you have a single point of managing mails and tickets.

[Recipient]: ../reference/pytanis/helpdesk/mail.md#pytanis.helpdesk.mail.Recipient
[Mail]: ../reference/pytanis/helpdesk/mail.md#pytanis.helpdesk.mail.Mail
[20_mail_to_reviewers_v1]: https://github.com/FlorianWilhelm/pytanis/blob/main/notebooks/pyconde-pydata-berlin-2023/20_mail_to_reviewers_v1.ipynb

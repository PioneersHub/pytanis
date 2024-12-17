import time

from pydantic import BaseModel, ConfigDict, validator
from tqdm.auto import tqdm


class MetaData(BaseModel):
    """Additional, arbitrary metadata provided by the user like for template filling"""

    model_config = ConfigDict(extra='allow')


class Recipient(BaseModel):
    """Details about the recipient

    Use the `data` field to store additional information
    """

    name: str
    email: str
    address_as: str | None = None  # could be the first name
    data: MetaData | None = None

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator('address_as')
    @classmethod
    def fill_with_name(cls, v, values):
        if v is None:
            v = values['name']
        return v


class Mail(BaseModel):
    """Mail template

    Use the `data` field to store additional information

    You can use the typical [Format String Syntax] and the objects `recipient` and `mail`
    to access metadata to complement the template, e.g.:

    ```
    Hello {recipient.address_as},

    We hope it's ok to address you your first name rather than using your full name being {recipient.name}.
    Have you read the email's subject '{mail.subject}'? How is your work right now at {recipient.data.company}?

    Cheers!
    ```

    [Format String Syntax]: https://docs.python.org/3/library/string.html#formatstrings
    """

    subject: str
    body: str
    recipients: list[Recipient]
    data: MetaData | None = None


class MailClient:
    """Mail client for mass mails via Mailgun"""

    batch_size: int = 10  # n messages are a batch
    wait_time: int = 20  # wait time after eacht batch before next

    def __init__(self):
        # TODO: add instantiation for Mailclient?
        pass

    # TODO: Check return type of mail
    def send(self, mail: Mail):
        """Send a mail to all recipients using Mailgun"""
        errors = []
        status_msg = None
        for idx, recipient in enumerate(tqdm(mail.recipients), start=1):
            try:
                pass
            except Exception as e:
                errors.append((recipient, e))

            if idx % self.batch_size == 0:
                time.sleep(self.wait_time)

        return status_msg, errors

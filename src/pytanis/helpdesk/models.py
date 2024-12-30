"""Return types of the HelpDesk / LiveChat API

Documentation: https://api.helpdesk.com/docs

ToDo:
    * Implement the types below correctly instead of using `Extra.Allow`
    * Find out why `extra=Extra.allow` causes mypy to fail. Seems like a bug in pydantic.
"""

from pydantic import BaseModel, ConfigDict


class Id(BaseModel):
    ID: str


class Agent(BaseModel):
    model_config = ConfigDict(extra='allow')


class Team(BaseModel):
    model_config = ConfigDict(extra='allow')


class Message(BaseModel):
    model_config = ConfigDict(extra='allow')

    text: str


class Requester(BaseModel):
    email: str
    name: str


class Assignment(BaseModel):
    model_config = ConfigDict(extra='allow')

    team: Id
    agent: Id


class NewTicket(BaseModel):
    """Object that needs to be sent when creating a NEW ticket"""

    model_config = ConfigDict(extra='allow')

    message: Message
    requester: Requester
    status: str | None = None  # ToDo: Rather use an Enum instead
    subject: str | None = None
    teamIDs: list[str] | None = None  # noqa: N815
    assignment: Assignment | None = None


class Ticket(BaseModel):
    """Actual ticket as returned by the API"""

    model_config = ConfigDict(extra='allow')

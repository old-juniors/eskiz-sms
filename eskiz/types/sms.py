from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from .base import EskizBaseModel
from .enums import MessageStatus

# MESSAGE


class Message(EskizBaseModel):
    to_: int = Field(..., alias="to")
    text: str
    user_sms_id: str


class Messages(EskizBaseModel):
    messages: List[Message]
    from_: str = Field(..., alias="from")
    dispatch_id: Union[str, int]


class MessageResponse(EskizBaseModel):
    id: str
    message: str
    status: Union[MessageStatus, List[MessageStatus]]


# BROADCAST MESSAGE


class _MessageStatus(EskizBaseModel):
    status: MessageStatus
    total: int


class BroadcastStatus(EskizBaseModel):
    status: str
    data: List[_MessageStatus]
    id: Any


# REPORT


class Report(EskizBaseModel):
    status: str
    month: str
    packets: int


class TotalMessages(EskizBaseModel):
    status: str
    data: List[Report]
    id: Any


# MESSAGE DETAILS


class Part(EskizBaseModel):
    accept: str
    status: str
    submit: int
    delivery: str


class Parts(EskizBaseModel):
    parts: Dict[str, Part]


class SmscData(EskizBaseModel):
    data: Dict[str, List[str]]


class Result(EskizBaseModel):
    id: int
    user_id: int
    country_id: Optional[int]
    connection_id: int
    smsc_id: int
    dispatch_id: Optional[Union[str, int]]
    user_sms_id: str
    request_id: str
    price: int
    is_ad: bool
    nick: str
    to_: str = Field(..., alias="to")
    message: str
    encoding: int
    parts_count: int
    parts: Parts
    status: str
    smsc_data: SmscData
    sent_at: str
    submit_sm_resp_at: str
    delivery_sm_at: str
    created_at: str
    updated_at: str


class Link(EskizBaseModel):
    url: Optional[str]
    label: str
    active: bool


class Data(EskizBaseModel):
    current_page: int
    path: str
    prev_page_url: Optional[str]
    first_page_url: str
    last_page_url: str
    next_page_url: Optional[str]
    per_page: int
    last_page: int
    from_: int = Field(..., alias="from")
    to_: int = Field(..., alias="to")
    total: int
    result: List[Result]
    links: List[Link]


class MessageDetails(EskizBaseModel):
    data: Data
    status: str

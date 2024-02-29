from typing import Any, List, Optional

from pydantic import Field

from .base import EskizBaseModel


class ResultItem(EskizBaseModel):
    id: int
    created_at: str
    updated_at: str
    user_id: int
    smsc_id: int
    template: str
    smsc: Any
    user: Any


class Link(EskizBaseModel):
    url: Optional[str]
    label: str
    active: bool


class Data(EskizBaseModel):
    current_page: int
    path: str
    prev_page_url: Any
    first_page_url: str
    last_page_url: str
    next_page_url: Any
    per_page: int
    last_page: int
    from_: int = Field(..., alias="from")
    to: int
    total: int
    result: List[ResultItem]
    links: List[Link]


class TemplateList(EskizBaseModel):
    status: str
    data: Data
    id: Any


class Template(EskizBaseModel):
    status: str
    data: ResultItem
    id: Any

from typing import Any

from .base import EskizBaseModel


class Data(EskizBaseModel):
    id: int
    created_at: str
    updated_at: str
    name: str
    email: str
    password: str
    role: str
    status: str
    is_vip: bool
    balance: int


class User(EskizBaseModel):
    status: str
    data: Data
    id: Any


class Balance(EskizBaseModel):
    balance: int


class UserLimit(EskizBaseModel):
    data: Balance
    status: str

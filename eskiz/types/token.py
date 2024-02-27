from .base import EskizBaseModel


class Data(EskizBaseModel):
    token: str


class TokenResponse(EskizBaseModel):
    message: str
    data: Data
    token_type: str

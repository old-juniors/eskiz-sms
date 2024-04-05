from typing import List, Optional


class EskizError(Exception):
    __subclasses: List = []
    match: Optional[str] = None
    text: Optional[str] = None

    @classmethod
    def get_text(cls):
        if cls.text is None and cls.match is not None:
            return cls.match.replace("_", " ").capitalize() + "!"
        return cls.text

    def __init_subclass__(cls, match: Optional[str] = None, **kwargs):
        super(EskizError, cls).__init_subclass__(**kwargs)
        if match is not None:
            cls.match = match.upper()
            cls.__subclasses.append(cls)

    @classmethod
    def detect(cls, description: str):
        """
        Automation detect error type.

        :param description:
        :raise: EskizError
        """
        match = description.upper()
        for err in cls.__subclasses:
            if err is cls:
                continue
            if err.match in match:
                raise err(err.get_text() or description)

        raise cls(description)


class AuthCredsInvalid(EskizError, match="AUTH_CREDS_INVALID"):
    pass


class BearerTokenInvalid(EskizError, match="BEARER_TOKEN_INVALID"):
    pass


class FieldsFormatInvalid(EskizError, match="FIELDS_FORMAT_INVALID"):
    pass


class UnknownMethod(EskizError, match="UNKNOWN_METHOD"):
    pass

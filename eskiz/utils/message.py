import uuid
from typing import List, Optional, Union

from eskiz.types.sms import Message, Messages
from eskiz.utils.fields import _generate_data


class MessageBuilder:
    def __init__(
        self,
        dispatch_id: Union[str, int],
        *,
        from_: str = "4546",
        messages: Optional[List[Message]] = None,
    ):
        self.messages = messages or []
        self.from_ = from_
        self.dispatch_id = dispatch_id

    def add(self, to: int, text: str, user_sms_id: Optional[str] = None):
        if user_sms_id is None:
            user_sms_id = str(uuid.uuid4())

        data = _generate_data(**locals())
        if isinstance(data, dict):
            self.messages.append(Message(**data))

    def as_messages(self) -> Messages:
        return Messages(
            messages=self.messages,
            from_=self.from_,  # type: ignore[call-arg]
            dispatch_id=self.dispatch_id,
        )

import asyncio
import contextlib
import logging
import ssl
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
import certifi
import jwt

from . import types
from .utils import exceptions
from .utils.fields import _generate_data
from .utils.methods import Methods

__all__ = ["SMSClient", "SERVICE_URL"]

SERVICE_URL = "notify.eskiz.uz"


class Token:
    """
    Represents an authentication token.

    - `__str__()`: Returns the string representation of the token.
    - `is_expired`: Checks if the token is expired.
    """

    def __init__(self, value: Union[Any, str, None]):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    @property
    def is_expired(self):
        """
        Checks if the token is expired.

        Returns:
         - bool: `True` if the token is expired, `False` otherwise.

        Raises:
         - `BearerTokenInvalid`: If an error occurs during token decoding.
        """
        try:
            options = {
                "verify_signature": False,
                "verify_exp": True,
            }
            jwt.decode(self.value, options=options)
            return False
        except jwt.ExpiredSignatureError:
            return True
        except jwt.PyJWTError:
            raise exceptions.BearerTokenInvalid()


class SMSClient:
    __context_token: ContextVar = ContextVar("EskizBearerToken")

    def __init__(
        self,
        token: Optional[str] = None,
        as_dict: bool = False,
        log_response: bool = False,
        service_url: str = SERVICE_URL,
        connections_limit: int = 100,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        json_serialize: Optional[Callable[..., Any]] = None,
        json_deserialize: Optional[Callable[..., Any]] = None,
    ):
        # Asyncio loop instance
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

        # JSON
        if not json_serialize or not json_deserialize:
            try:
                import ujson as json  # type: ignore
            except ImportError:
                import json  # type: ignore[no-redef]

            if json_serialize is None:
                json_serialize = json.dumps
            if json_deserialize is None:
                json_deserialize = json.loads

        self._json_serialize = json_serialize
        self._json_deserialize = json_deserialize

        # URL's
        self._service = None
        self._api_url = None
        self._service_url = None
        self.service = service_url

        # aiohttp main session
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        connector = aiohttp.TCPConnector(
            limit=connections_limit, ssl=ssl_context, loop=self.loop
        )

        self.session = aiohttp.ClientSession(
            connector=connector, loop=self.loop, json_serialize=json_serialize
        )

        self._token = token
        self.as_dict = as_dict

        self.log_response = log_response

        if log_response:
            logging.basicConfig(
                encoding="utf-8",
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
            )

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, value: str):
        if "." not in value or "://" in value:
            raise ValueError(f"Invalid service URL: {value}")

        value = value.rstrip("/")

        self._service = value
        self._service_url = f"https://{value}"
        self._api_url = f"https://{value}/api/"

    @property
    def api_url(self):
        return self._api_url

    @property
    def service_url(self):
        return self._service_url

    def format_api_url(self, method: str, path: str):
        return method, str(self.api_url) + path

    async def handle_error(self, error_text=None):
        await self.close()  # close session
        raise exceptions.EskizError.detect(error_text)

    async def request(
        self,
        method: Dict,
        *,
        payload: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict] = None,
    ):
        _method, url = self.format_api_url(**method)

        async with self.session.request(
            method=_method,
            url=url,
            data=payload,
            headers=headers,
        ) as response:

            json_data = await response.json(loads=self._json_deserialize)

            if self.log_response:
                logging.info(str(json_data))

            if "status" in json_data and json_data["status"] == "fail":
                error_text = json_data["data"]["alert"]
                await self.handle_error(error_text)

            if len(json_data) == 1 and "message" in json_data:
                await self.handle_error("AUTH_CREDS_INVALID")

        return json_data

    @property
    def token(self) -> Token:
        return Token(self.__context_token.get(None) or self._token)

    @token.setter
    def token(self, token: str):
        if isinstance(token, str):
            self._token = token
        else:
            raise TypeError("value must be an 'str'")

    @token.deleter
    def token(self):
        self._token = None

    @contextlib.contextmanager
    def with_token(self, token: str):
        """
        Manage token contexts easily for temporary changes.

        ```
        # Will change token in current context
        with client.with_token('foo'):
            print(f"Inside context manager: '{client.token}'")
        ```
        Args: token (str)
        """
        context_token = self.__context_token.set(token)
        yield
        self.__context_token.reset(context_token)

    async def close(self) -> None:
        """
        Closes the session.
        """
        await self.session.close()

    def _set_header_token(self, token: Optional[str]):
        headers: Dict[str, str] = {}

        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")

        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    async def get_token(
        self, email: str, password: str, *, auth: bool = True
    ) -> str:
        """For authorization use this API, returns a token

        Args:
            - email (str): `your@email.uz`
            - password (str): `your_secret_code_from_cabinet`
            - auth (bool, optional): Defaults to True.

        Returns:
            str: token
        """
        payload = _generate_data(**locals())
        raw = await self.request(Methods.GET_TOKEN, payload=payload)
        response = types.TokenResponse(**raw)

        if auth:
            self._token = response.data.token

        return self.token.__str__()

    async def refresh_token(
        self, token: Optional[str] = None, auth: bool = True
    ) -> str:
        """Updates the current token

        Args:
            - auth (bool, optional): Defaults to True.

        Returns:
            _type_: str
        """
        headers = self._set_header_token(token)
        raw = await self.request(Methods.REFRESH_TOKEN, headers=headers)
        response = types.TokenResponse(**raw)

        if auth:
            self._token = response.data.token

        return self.token.__str__()

    async def get_user_data(
        self, token: Optional[str] = None
    ) -> Union[types.User, Dict]:
        """Returns all user data

        Returns:
            Union[types.User, Dict]
        """
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_USER_DATA, headers=headers)

        if self.as_dict:
            return raw

        return types.User(**(raw or {}))

    async def get_template(
        self, id: Union[int, str], *, token: Optional[str] = None
    ) -> Union[types.Template, Dict]:
        """Get template by ID

        Args:
            - id (Union[int, str])

        Returns:
            Union[types.Template, Dict]
        """
        headers = self._set_header_token(token)

        method = Methods.GET_TEMPLATE

        path = method.get("path")
        if isinstance(path, str):
            method["path"] = path.format(id=id)

        raw = await self.request(method, headers=headers)

        if self.as_dict:
            return raw

        return types.Template(**(raw or {}))

    async def get_template_list(
        self, token: Optional[str] = None
    ) -> Union[types.TemplateList, Dict]:
        """Get all templates

        Returns:
            Union[types.TemplateList, Dict]
        """
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_TEMPLATE_LIST, headers=headers)

        if self.as_dict:
            return raw

        return types.TemplateList(**(raw or {}))

    async def send_sms(
        self,
        mobile_phone: Union[str, int],
        message: str,
        *,
        from_: str = "4546",
        callback_url: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Union[types.MessageResponse, Dict]:
        """Send SMS

        Args:
            - mobile_phone (Union[str, int])
            - message (str)
            - from_ (str, optional): Defaults to '4546'.
            - callback_url (Optional[str], optional): Defaults to None.
            - You can provide a callback URL where you will receive POST data in the following format:

            ```json
            {
              "message_id": "4385062",
              "user_sms_id": "vash_ID_zdes",
              "country": "UZ",
              "phone_number": "998991234567",
              "sms_count": "1",
              "status": "DELIVRD",
              "status_date": "2021-04-02 00:39:36"
            }
            ```

        Returns:
            Union[types.MessageResponse, Dict]
        """
        payload = _generate_data(**locals(), exclude=["token"])
        headers = self._set_header_token(token)

        raw = await self.request(
            Methods.SEND_SMS, payload=payload, headers=headers
        )

        if self.as_dict:
            return raw

        return types.MessageResponse(**raw)

    async def send_batch_sms(
        self, to: types.Messages, *, token: Optional[str] = None
    ) -> Union[types.MessageResponse, Dict]:
        """Broadcast

        Args:
            - to (types.Messages)

        Use `MessageBuilder`:
        ```py
        users = [1, 2, 3]
        msg_builder = MessageBuilder()

        for user in users:
            msg_builder.add(to=user, text="hi")

        messages = msg_builder.as_messages()
        ```

        Returns:
            Union[types.MessageResponse, Dict]:
        """
        headers = self._set_header_token(token)
        json = to.model_dump_json(by_alias=True)
        payload = self._json_serialize(json)

        raw = await self.request(
            Methods.SEND_BATCH_SMS, payload=payload, headers=headers
        )

        if self.as_dict:
            return raw

        return types.MessageResponse(**raw)

    async def send_international_sms(
        self,
        mobile_phone: Union[str, int],
        message: str,
        country_code: str,
        *,
        callback_url: Optional[str] = None,
        unicode: int = 0,
        token: Optional[str] = None,
    ) -> Dict:
        """Using this API you can send SMS to foreign countries around the world.

        Args:
            - mobile_phone (Union[str, int])
            - message (str)
            - country_code (str)
            - callback_url (Optional[str], optional): Defaults to None.
            - unicode (int, optional): Defaults to 0.

        Returns:
            Dict
        """
        payload = _generate_data(
            **locals(), exclude=["token"], is_payload=True
        )
        headers = self._set_header_token(token)

        raw = await self.request(
            Methods.SEND_INTERNATIONAL_SMS, payload=payload, headers=headers
        )

        if self.as_dict:
            return raw

        # TODO
        return raw

    async def get_message_details(
        self,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        *,
        page_size: int = 20,
        count: int = 0,
        token: Optional[str] = None,
    ) -> Union[types.MessageDetails, Dict]:
        """Message Detailing

        Args:
            - start_date (Union[str, datetime])
            - end_date (Union[str, datetime])
            - page_size (int, optional) Defaults to 20.
            - count (int, optional) Defaults to 0.

        Returns:
            Union[types.MessageDetails, Dict]
        """
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d %H:%M")

        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d %H:%M")

        payload = _generate_data(**locals(), exclude=["token"])
        headers = self._set_header_token(token)

        raw = await self.request(
            Methods.GET_MESSAGE_DETAILS, payload=payload, headers=headers
        )

        if self.as_dict:
            return raw

        return types.MessageDetails(**(raw or {}))

    async def get_message_by_dispatch(
        self,
        user_id: int,
        dispatch_id: Union[str, int],
        *,
        token: Optional[str] = None,
    ):
        """Receive all sent SMS via ID mailing

        Args:
            - user_id (int)
            - dispatch_id (Union[str, int])

        Returns:
            Union[types.MessageDetails, Dict]
        """
        payload = _generate_data(**locals(), exclude=["token"])
        headers = self._set_header_token(token)

        raw = await self.request(
            Methods.GET_MESSAGE_BY_DISPATCH, payload=payload, headers=headers
        )

        if self.as_dict:
            return raw

        return types.MessageDetails(**(raw or {}))

    async def get_dispatch_status(
        self,
        user_id: int,
        dispatch_id: Union[str, int],
        *,
        token: Optional[str] = None,
    ) -> Union[types.BroadcastStatus, Dict]:
        """Get broadcast status

        Args:
            - user_id (int)
            - dispatch_id (Union[str, int])

        Returns:
            Union[types.BroadcastStatus, Dict]
        """
        payload = _generate_data(**locals(), exclude=["token"])
        headers = self._set_header_token(token)

        raw = await self.request(
            Methods.GET_DISPATCH_STATUS, payload=payload, headers=headers
        )

        if self.as_dict:
            return raw

        return types.BroadcastStatus(**(raw or {}))

    async def get_nick_list(self, token: Optional[str] = None) -> List[str]:
        """Get nickname list

        Returns:
            List[str]: Example: `["Eskiz.uz", "Old.Juniors"]`
        """
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_NICK_LIST, headers=headers)

        return raw

    async def get_sms_totals(
        self,
        year: int,
        month: int,
        *,
        is_global: int = 0,
        token: Optional[str] = None,
    ) -> Union[types.TotalMessages, Dict]:
        """SMS Totals

        Args:
            - year (int)
            - month (int)
            - is_global (int, optional) Defaults to 0.

        Returns:
            Union[types.TotalMessages, Dict]
        """
        filters = _generate_data(
            **locals(), exclude=["token"], is_payload=False
        )
        headers = self._set_header_token(token)

        method = Methods.GET_SMS_TOTALS

        path = method.get("path")
        if isinstance(path, str) and isinstance(filters, str):
            method["path"] += "?" + filters

        raw = await self.request(method, headers=headers)

        if self.as_dict:
            return raw

        return types.TotalMessages(**raw)

    async def get_limit(
        self, token: Optional[str] = None
    ) -> Union[types.UserLimit, Dict]:
        """Get Limit

        Returns:
            Union[types.UserLimit, Dict]
        """
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_LIMIT, headers=headers)

        if self.as_dict:
            return raw

        return types.UserLimit(**(raw or {}))

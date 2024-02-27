import asyncio
import contextlib
import logging
import ssl
from contextvars import ContextVar
from datetime import datetime
from typing import List, Optional, Union

import aiohttp
import certifi
import jwt

from . import types
from .utils import exceptions
from .utils.fields import _generate_data
from .utils.methods import Methods

logger = logging.getLogger(__name__)

SERVICE_URL = 'notify.eskiz.uz'


class Token:
    def __init__(self, value):
        self.value = value

    @property
    def is_expired(self):
        if not self.value:
            return True
        try:
            jwt.decode(
                self.value,
                options={
                    "verify_signature": False,
                    "verify_exp": True
                }
            )
            return False
        except jwt.ExpiredSignatureError:
            return True
        except jwt.PyJWTError:
            raise exceptions.BearerTokenInvalid()

    def __str__(self):
        return self.value


class SMSClient:
    __context_token = ContextVar('EskizBearerToken')

    def __init__(
        self,
        token: Optional[str] = None,
        as_dict: bool = False,
        service_url: str = SERVICE_URL,
        connections_limit: Optional[int] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        loop: asyncio.AbstractEventLoop = None,
        json_serialize: callable = None,
        json_deserialize: callable = None
    ):
        # Asyncio loop instance
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

        # JSON
        if not json_serialize or not json_deserialize:
            try:
                import ujson as json
            except ImportError:
                import json

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

        # Proxy settings
        self.proxy = proxy
        self.proxy_auth = proxy_auth

        # aiohttp main session
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        if isinstance(proxy, str) and proxy.startswith(('socks5://', 'socks4://')):
            from aiohttp_socks import SocksConnector
            from aiohttp_socks.utils import parse_proxy_url

            socks_ver, host, port, username, password = parse_proxy_url(proxy)
            if proxy_auth:
                if not username:
                    username = proxy_auth.login
                if not password:
                    password = proxy_auth.password

            connector = SocksConnector(
                socks_ver=socks_ver, host=host, port=port,
                username=username, password=password,
                limit=connections_limit, ssl_context=ssl_context,
                rdns=True, loop=self.loop
            )

            self.proxy = None
            self.proxy_auth = None
        else:
            connector = aiohttp.TCPConnector(
                limit=connections_limit,
                ssl=ssl_context,
                loop=self.loop
            )

        self.session = aiohttp.ClientSession(
            connector=connector, loop=self.loop,
            json_serialize=json_serialize
        )

        self._token = token
        self.as_dict = as_dict

    @property
    def service(self) -> str:
        return self._service

    @service.setter
    def service(self, value: str):
        if '.' not in value or '://' in value:
            raise ValueError(f"Invalid service URL: {value}")

        value = value.rstrip('/')

        self._service = value
        self._service_url = f"https://{value}"
        self._api_url = f"https://{value}/api/"

    @property
    def api_url(self) -> str:
        return self._api_url

    @property
    def service_url(self) -> str:
        return self._service_url

    def format_api_url(self, method: str, path: str):
        return method, self.api_url + path

    async def handle_error(self, error_text=None):
        await self.close()  # close session
        raise exceptions.EskizError.detect(error_text)

    async def request(
        self, method: dict, *,
        payload: Optional[dict] = None,
        headers: Optional[dict] = None
    ):
        _method, url = self.format_api_url(**method)

        async with self.session.request(
            method=_method, url=url,
            data=payload, headers=headers,
            proxy_auth=self.proxy_auth,
            proxy=self.proxy
        ) as response:

            json_data = await response.json(loads=self._json_deserialize)

            if 'status' in json_data and json_data['status'] == 'fail':
                error_text = json_data['data']['alert']
                await self.handle_error(error_text)

            if len(json_data) == 1 and 'message' in json_data:
                await self.handle_error('BEARER_TOKEN_INVALID')

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
    def with_token(self, token):
        context_token = self.__context_token.set(token)
        yield
        self.__context_token.reset(context_token)

    async def close(self) -> None:
        await self.session.close()

    def _set_header_token(self, token: Optional[str]):
        headers = {}
        if self.token:
            headers.setdefault('Authorization', f'Bearer {self.token}')

        if token:
            headers['Authorization'] = f'Bearer {token}'

        return headers

    async def get_token(
        self,
        email: str,
        password: str,
        *,
        auth: bool = True
    ):
        payload = _generate_data(**locals())
        raw = await self.request(Methods.GET_TOKEN, payload=payload)
        response = types.TokenResponse(**raw)

        if auth:
            self.token = response.data.token

        return self.token

    async def refresh_token(
        self,
        token: Optional[str] = None,
        auth: bool = True
    ):
        headers = self._set_header_token(token)
        raw = await self.request(Methods.REFRESH_TOKEN, headers=headers)
        response = types.TokenResponse(**raw)

        if auth:
            self.token = response.data.token

        return self.token

    async def get_user_data(self, token: Optional[str] = None):
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_USER_DATA, headers=headers)

        if self.as_dict:
            return raw

        return types.User(**(raw or {}))

    async def get_template(self, id, *, token: Optional[str] = None):
        headers = self._set_header_token(token)

        method = Methods.GET_TEMPLATE
        method['path'] = method.get('path').format(id=id)

        raw = await self.request(method, headers=headers)

        if self.as_dict:
            return raw

        return types.Template(**(raw or {}))

    async def get_template_list(self, token: Optional[str] = None):
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
        from_: str = '4546',
        callback_url: Optional[str] = None,
        token: Optional[str] = None
    ):
        payload = _generate_data(**locals(), exclude=['token'])
        headers = self._set_header_token(token)

        raw = await self.request(Methods.SEND_SMS, payload=payload, headers=headers)

        if self.as_dict:
            return raw

        return types.MessageResponse(**raw)

    async def send_batch_sms(
        self,
        to: types.Messages,
        *,
        token: Optional[str] = None
    ):
        headers = self._set_header_token(token)
        json = to.model_dump_json(by_alias=True)
        payload = self._json_serialize(json)

        raw = await self.request(Methods.SEND_BATCH_SMS, payload=payload, headers=headers)

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
        token: Optional[str] = None
    ):
        payload = _generate_data(**locals(), exclude=['token'])
        headers = self._set_header_token(token)

        raw = await self.request(Methods.SEND_INTERNATIONAL_SMS, payload=payload, headers=headers)

        if self.as_dict:
            return raw

        # TODO

    async def get_message_details(
        self,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        *,
        page_size: int = 20,
        count: int = 0,
        token: Optional[str] = None
    ):
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d %H:%M")

        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d %H:%M")

        payload = _generate_data(**locals(), exclude=['token'])
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_MESSAGE_DETAILS, payload=payload, headers=headers)

        if self.as_dict:
            return raw

        return types.MessageDetails(**(raw or {}))

    async def get_message_by_dispatch(
        self,
        user_id: int,
        dispatch_id: Union[str, int],
        *,
        token: Optional[str] = None
    ):
        payload = _generate_data(**locals(), exclude=['token'])
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_MESSAGE_BY_DISPATCH, payload=payload, headers=headers)

        if self.as_dict:
            return raw

        return types.MessageDetails(**(raw or {}))

    async def get_dispatch_status(
        self,
        user_id: int,
        dispatch_id: Union[str, int],
        *,
        token: Optional[str] = None
    ):
        payload = _generate_data(**locals(), exclude=['token'])
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_DISPATCH_STATUS, payload=payload, headers=headers)

        if self.as_dict:
            return raw

        return types.BroadcastStatus(**(raw or {}))

    async def get_nick_list(self, token: Optional[str] = None) -> List[str]:
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_NICK_LIST, headers=headers)

        return raw

    async def get_sms_totals(
        self,
        year: int,
        month: int,
        *,
        is_global: int = 0,
        token: Optional[str] = None
    ):
        filters = _generate_data(
            **locals(), exclude=['token'], is_payload=False)
        headers = self._set_header_token(token)

        method = Methods.GET_SMS_TOTALS
        method['path'] = method.get('path') + '?' + filters

        raw = await self.request(method, headers=headers)

        if self.as_dict:
            return raw

        return types.TotalMessages(**raw)

    async def get_limit(self, token: Optional[str] = None):
        headers = self._set_header_token(token)

        raw = await self.request(Methods.GET_LIMIT, headers=headers)

        if self.as_dict:
            return raw

        return types.UserLimit(**(raw or {}))

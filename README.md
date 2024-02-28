## Eskiz SMS Gateway Python SDK (BETA)

## Features

- Token Management: Auto auth and refresh expired tokens.
- Message Building: Construct messages efficiently with `MessageBuilder`.
- Token Context Management: Manage token contexts easily for temporary changes.
- Synchronous Wrapper: Utilize synchronous capabilities with `sync.force_sync`.

> [!WARNING]
> We're currently in beta, actively refining our features.

---

## Installation

```
pip install eskiz-sms-client
```

---

## Quickstart

Example for auth get token:

```py
import asyncio

from eskiz import SMSClient

async def main():
  client = SMSClient()
  await client.get_token('test@eskiz.uz', 'password')

  print(client.token) # NEW TOKEN

asyncio.run(main())
```

Example for refresh token:

```py
if client.token.is_expired:
  await client.refresh_token()

print(client.token) # REFRESHED TOKEN
```

Example for send SMS:

```py
from eskiz import SMSClient

client = SMSClient(token='TOKEN', as_dict=False)

response = await client.send_sms(
  mobile_phone=998991234567,
  message="test from sdk"
)
print(response.status) # 'waiting'

# current response as dict
print(response.model_dump())

# { "id": "<id>", "status": "waiting", "message": "Waiting for SMS provider" }
```

> [!TIP]
> set `as_dict` to `True`, all responses will be returned as dict

## More Examples

In examples diriectory: [see](https://github.com/old-juniors/eskiz-sms/tree/main/examples)

## Documentation

https://documenter.getpostman.com/view/663428/RzfmES4z

import asyncio

from eskiz import SMSClient
from eskiz.utils.message import MessageBuilder


async def main():
    client = SMSClient()

    # AUTH (GET TOKEN)
    await client.get_token(
        email='EMAIL',
        password='PASSWORD'
    )
    print(client.token)

    # REFRESH TOKEN
    if client.token.is_expired:
        await client.refresh_token()

    # SEND SMS
    response = await client.send_sms(
        mobile_phone=998991234567,
        message="test from sdk"
    )
    print(response)

    # MessageBuilder USAGE:
    users = [998991234567, 998991234568, 998991234569]

    message_builder = MessageBuilder(dispatch_id=123)

    for user in users:
        message_builder.add(to=user, text="hi")

    user_messages = message_builder.as_messages()
    print(user_messages)

    # SEND BATCH SMS
    response = await client.send_batch_sms(to=user_messages)
    print(response)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())

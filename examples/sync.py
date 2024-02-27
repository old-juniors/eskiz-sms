from eskiz import SMSClient
from eskiz.utils import sync


@sync.force_sync
async def some_call():
    client = SMSClient('TOKEN')

    response = await client.get_user_data()

    print(response)

    await client.close()


some_call()

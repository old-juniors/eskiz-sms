from eskiz import SMSClient
from eskiz.utils import sync


@sync.force_sync
async def some_call():
    # Initialize SMS client with provided token
    client = SMSClient('TOKEN')

    # Retrieve user data asynchronously
    response = await client.get_user_data()

    # Print user data
    print(response)

    # Close the client connection
    await client.close()

# Execute the function
some_call()

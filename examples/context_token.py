import asyncio

from eskiz import SMSClient

client = SMSClient("token")

print(f"1. Root: '{client.token}'")
with client.with_token("foo"):  # Will change token in current context
    print(f"2. Inside context manager: '{client.token}'")

    # Will change token in current context
    with client.with_token("bar"):
        print(f"3. Inside child context manager: '{client.token}'")
        client.token = "baz"  # Doesn't affect token inside current context
        print(
            f"4. After changing: '{client.token}' (is not changed inside context)"
        )

    print(f"5. Inside context manager: '{client.token}'")

print(f"6. Root: '{client.token}'")  # Shows changed token

asyncio.run(client.close())

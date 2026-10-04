"""Each marked public-client misuse must be rejected by mypy; never execute this file."""

from taruvi import Client, FunctionExecutionResponse

API_URL = "https://example.invalid"
APP = "typing-probe"


async def await_contract_misuses() -> None:
    sync = Client(API_URL, APP, mode="sync")
    asynchronous = Client(API_URL, APP, mode="async")
    await sync.functions.execute("sample")  # expect-error: misc
    pending = asynchronous.functions.execute("sample")
    result: FunctionExecutionResponse = pending  # expect-error: assignment
    await asynchronous.auth.signInWithToken("token")  # expect-error: misc
    await sync.auth.signInWithPassword("email", "password")  # expect-error: misc
    closed: None = asynchronous.close()  # expect-error: assignment
    with asynchronous:  # expect-error: attr-defined, attr-defined
        pass
    async with sync:  # expect-error: attr-defined, attr-defined
        pass
    print(result, closed)


def autodetection_is_not_assumed_sync() -> None:
    automatic = Client(API_URL, APP)
    response = automatic.functions.execute("sample")
    result: FunctionExecutionResponse = response  # expect-error: assignment
    print(result)

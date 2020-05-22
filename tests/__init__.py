import asyncio


async def assert_received_eventually(receiver, expected):
    i = 0
    while True:
        try:
            assert receiver.received == expected, receiver.received
            receiver.received = []  # reset again
            break
        except AssertionError as err:
            if i < 5:
                i += 1
                await asyncio.sleep(0.1)
            else:
                raise err

import asyncio
import logging


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


def warn_messages(caplog):
    return [x.message for x in caplog.records if x.levelno == logging.WARNING]


def error_messages(caplog):
    return [x.message for x in caplog.records if x.levelno == logging.ERROR]

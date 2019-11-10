import asyncio

from contextlib import suppress

from testandconquer import logger
from testandconquer.client import Client


class Heartbeat:
    def __init__(self, settings):
        self.client = Client(settings)
        self.client.api_retries = 0  # no need to retry a heartbeat

    def start(self):
        self.task = asyncio.ensure_future(self._heartbeat_task())

    async def stop(self):
        self.task.cancel()
        with suppress(asyncio.CancelledError):
            await self.task

    async def _heartbeat_task(self):
        logger.debug('initialising heartbeat task')
        while True:
            logger.debug('sending heartbeat')
            try:
                asyncio.get_event_loop().run_in_executor(None, self.client.post, '/heartbeat', None)
            except asyncio.CancelledError:
                break
            except BaseException:
                logger.error('heartbeat to server failed')
            await asyncio.sleep(10)

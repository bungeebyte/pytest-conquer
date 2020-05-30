import asyncio

from testandconquer.client import Client
from testandconquer.vendor import websockets


HOST = '0.0.0.0'
PORT = 4352


class MockServer():
    def __init__(self):
        self.daemon = True
        self.stopping = False
        self.server = None
        self.producer_task = None
        self.consumer_task = None
        self.outgoing = asyncio.Queue()
        self.received = []
        self.connections = []

    async def start(self):
        self.server = await websockets.serve(self._handle, HOST, PORT, process_request=self._process_request)

    async def stop(self):
        self.stopping = True
        await asyncio.wait_for(self.outgoing.join(), timeout=1)
        self.server.close()
        await self.server.wait_closed()
        if (self.consumer_task):
            self.consumer_task.cancel()
        if (self.producer_task):
            self.producer_task.cancel()

    async def restart(self):
        await self.stop()
        await self.start()

    async def _process_request(self, path, request_headers):
        self.connections.append((path, request_headers))
        pass

    async def _handle(self, ws, path):
        async def consumer_handler():
            async for raw_message in ws:
                message = Client.decode(raw_message)
                self.received.append((message['type'], message['payload']))

        async def producer_handler():
            while True:
                message = await self.outgoing.get()
                await ws.send(message)
                self.outgoing.task_done()

        while not self.stopping:
            self.consumer_task = asyncio.ensure_future(consumer_handler())
            self.producer_task = asyncio.ensure_future(producer_handler())
            done, pending = await asyncio.wait([self.consumer_task, self.producer_task], return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()

    async def send(self, message_type, payload):
        await self.outgoing.put(Client.encode(0, message_type, payload))

    @property
    def url(self):
        return '%s:%i' % (HOST, PORT)

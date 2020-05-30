from testandconquer.client import Client


class MockClient(Client):

    def __init__(self, settings):
        super().__init__(settings)
        self.received = []

    async def start(self):
        pass

    async def stop(self):
        pass

    async def send(self, type, payload):
        self.received.append((type, payload))

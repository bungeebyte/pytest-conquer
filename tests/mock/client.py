from testandconquer.client import Client


class MockClient(Client):

    def __init__(self, settings):
        super().__init__(settings)

    def start(self):
        pass

    def stop(self):
        pass

    def send(self, type, payload):
        self.received.append((type, payload))

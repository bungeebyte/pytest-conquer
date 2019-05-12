from testandconquer.settings import Settings


class MockSettings(Settings):
    def __init__(self, args):
        super().__init__(args)

    # skips network call and validation
    def init_env(self, _client=None):
        pass

from testandconquer.settings import Settings


class MockSettings(Settings):
    def __init__(self, args={}):
        super().__init__(args)

    # let's skip this
    def init_env(self):
        pass

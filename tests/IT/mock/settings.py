from testandconquer.settings import Settings


class MockSettings(Settings):
    def __init__(self, env):
        super().__init__(env)

    # let's skip this
    def init_env(self):
        pass

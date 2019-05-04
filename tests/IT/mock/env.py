from testandconquer.env import Env


class MockEnv(Env):
    def __init__(self, args={}):
        super().__init__(args)

    def init_mapping(self, settings):
        pass  # would normally make an HTTP call

    def get(self, name):
        return self.args.get(name, None)  # ignore all other sources

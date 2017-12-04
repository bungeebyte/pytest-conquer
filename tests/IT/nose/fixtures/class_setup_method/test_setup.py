class TestObject(object):

    def setup(self):
        self.is_setup = True

    def test(self):
        assert self.is_setup

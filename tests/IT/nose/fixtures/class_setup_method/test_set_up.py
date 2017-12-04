class TestObject(object):

    def setUp(self):
        self.is_setup = True

    def test(self):
        assert self.is_setup

class TestObject(object):

    def setup_method(self, method):
        raise Exception('setup failed')

    def test(self):
        pass

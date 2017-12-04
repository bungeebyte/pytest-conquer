class TestObject(object):

    def teardown_method(self, method):
        raise Exception('teardown failed')

    def test(self):
        pass

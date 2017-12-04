class TestObject(object):

    @classmethod
    def teardown_class(cls):
        raise Exception('teardown failed')

    def test(self):
        assert 2 + 2 == 4

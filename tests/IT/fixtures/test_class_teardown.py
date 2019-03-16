class TestObject(object):

    @classmethod
    def teardown_class(cls):
        pass

    def test(self):
        assert 2 + 2 == 4

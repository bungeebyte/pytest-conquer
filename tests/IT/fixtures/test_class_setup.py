setup = 0


class TestObject(object):

    @classmethod
    def setup_class(cls):
        global setup
        setup += 1

    def test1(self):
        global setup
        assert setup == 1

    def test2(self):
        global setup
        assert setup == 1

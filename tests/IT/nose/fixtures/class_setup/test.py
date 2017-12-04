is_setup = False


class TestObject(object):

    @classmethod
    def setup_class(cls):
        global is_setup
        is_setup = True

    def test(self):
        global is_setup
        assert is_setup

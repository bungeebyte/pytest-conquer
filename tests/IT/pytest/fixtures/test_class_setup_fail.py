class TestObject(object):

    @classmethod
    def setup_class(cls):
        do_some_setup()

    def test(self):
        assert 2 + 2 == 4


def do_some_setup():
    raise Exception('setup failed')

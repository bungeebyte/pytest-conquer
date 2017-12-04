from nose.tools import with_setup


def teardown_function():
    pass


@with_setup(None, teardown_function)
def test():
    pass

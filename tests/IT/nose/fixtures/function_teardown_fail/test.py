from nose.tools import with_setup


def teardown_function():
    raise RuntimeError('teardown failed')


@with_setup(None, teardown_function)
def test():
    pass

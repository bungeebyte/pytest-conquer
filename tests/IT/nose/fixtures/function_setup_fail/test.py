from nose.tools import with_setup


def setup_function():
    raise RuntimeError('setup failed')


@with_setup(setup_function)
def test():
    pass

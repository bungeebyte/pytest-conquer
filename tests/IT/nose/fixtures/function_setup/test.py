from nose.tools import with_setup

is_setup = False


def setup_function():
    global is_setup
    is_setup = True


@with_setup(setup_function)
def test():
    global is_setup
    assert is_setup

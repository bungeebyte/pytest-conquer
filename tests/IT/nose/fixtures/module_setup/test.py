is_setup = False


def setup_module():
    global is_setup
    is_setup = True


def test():
    global is_setup
    assert is_setup

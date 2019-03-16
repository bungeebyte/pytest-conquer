setup = 0


def teardown_module(module):
    global setup
    assert setup == 1


def test():
    global setup
    setup += 1

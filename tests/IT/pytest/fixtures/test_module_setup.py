setup = 0


def setup_module(module):
    global setup
    setup += 1


def test1():
    global setup
    assert setup == 1


def test2():
    global setup
    assert setup == 1

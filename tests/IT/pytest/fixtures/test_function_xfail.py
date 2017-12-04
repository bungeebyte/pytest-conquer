import pytest


@pytest.mark.xfail
def test_xfail():
    assert 1 + 2 == 12

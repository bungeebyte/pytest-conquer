import pytest


@pytest.mark.skip()
def test_skip():
    assert 1 + 2 == 12

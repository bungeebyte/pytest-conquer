import pytest


@pytest.mark.tag
def test_pass():
    assert 2 + 2 == 4

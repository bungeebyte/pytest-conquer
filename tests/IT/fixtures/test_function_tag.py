import pytest


@pytest.mark.conquer(group='test')
@pytest.mark.other_mark  # will be ignored
def test_pass():
    assert 2 + 2 == 4

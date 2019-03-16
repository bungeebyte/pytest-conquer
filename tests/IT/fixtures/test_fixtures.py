import pytest


@pytest.fixture
def fixture1():
    return True


@pytest.fixture
def fixture2():
    return True


def test_with_fixtures(fixture1, fixture2):
    assert fixture1
    assert fixture2

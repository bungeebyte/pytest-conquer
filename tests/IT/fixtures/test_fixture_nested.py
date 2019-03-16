import pytest


@pytest.fixture
def fixture1():
    return 1


@pytest.fixture
def fixture2(fixture1):
    return fixture1 + 1


def test_with_fixture(fixture2):
    assert fixture2 == 2

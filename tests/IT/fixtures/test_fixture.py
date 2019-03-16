import pytest


@pytest.fixture
def fixture():
    return True


def test_with_fixture(fixture):
    assert fixture

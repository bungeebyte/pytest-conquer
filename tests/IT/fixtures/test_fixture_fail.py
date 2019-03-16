import pytest


@pytest.fixture
def fixture():
    raise Exception('setup failed')


def test_with_fixture(fixture):
    assert 1 == 2

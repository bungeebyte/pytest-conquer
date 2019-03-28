import pytest


@pytest.fixture()
@pytest.mark.tag()
def fixture():
    return 1


def test_with_fixture(fixture):
    assert fixture == 1

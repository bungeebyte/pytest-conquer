import pytest


@pytest.fixture()
@pytest.mark.conquer(group='my_group', singleton=True)
def fixture():
    return 1


def test_with_fixture(fixture):
    assert fixture == 1

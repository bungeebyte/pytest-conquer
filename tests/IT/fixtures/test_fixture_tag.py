import pytest


@pytest.fixture()
@pytest.mark.tag(arg1='1', arg2=2)
def fixture():
    return 1


def test_with_fixture(fixture):
    assert fixture == 1

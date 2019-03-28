import pytest


@pytest.fixture(params=[2, 4])
def fixture(request):
    return request.param


def test_with_fixture(fixture):
    assert fixture % 2 == 0

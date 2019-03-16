import pytest
from fixture import fixture_import  # noqa


@pytest.mark.usefixtures('fixture_import')
def test_with_fixture():
    pass

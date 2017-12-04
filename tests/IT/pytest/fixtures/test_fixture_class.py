import pytest


@pytest.mark.usefixtures('fixture_session')
class TestObject(object):

    def test(self):
        assert 2 + 2 == 4

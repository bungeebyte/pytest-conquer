import pytest


@pytest.mark.conquer(group='my_group')
class TestObject(object):

    def test(self):
        assert 2 + 2 == 4

import pytest


class TestObject(object):

    @classmethod
    @pytest.mark.conquer(group='my_group')
    def setup_class(cls):
        pass

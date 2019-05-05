import pytest


class TestObject(object):

    @pytest.mark.parametrize('test_input,expected', [
        ('3+5', 8),
        ('2+4', 6),
    ])
    def test_param(self, test_input, expected):
        assert eval(test_input) == expected

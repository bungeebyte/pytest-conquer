from unittest.mock import patch


class TestObject(object):

    @patch('os.listdir')
    @patch('os.listdir')
    def test(self, _mock1, _mock2):
        assert 2 + 2 == 4

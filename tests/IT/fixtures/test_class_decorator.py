from unittest.mock import patch


class TestObject(object):

    @patch('os.listdir')
    def test(self, _mock1):
        assert 2 + 2 == 4

import pytest

from testandconquer.client import Client

from tests.mock.settings import MockSettings


MOCK_CONTENT = """{"message": "Hello world!"}""".encode()


class TestClient():

    def test_send_successfully(self):
        client = MockClient([(MockResponse(200), MOCK_CONTENT)])
        res = client.post('/endpoint', {})
        assert res == {'message': 'Hello world!'}

    def test_retry_on_404(self):
        client = MockClient([
            (MockResponse(404), MOCK_CONTENT),
            (MockResponse(200), MOCK_CONTENT),
        ])
        res = client.post('/endpoint', {})
        assert res == {'message': 'Hello world!'}

    def test_do_not_retry_on_400(self):
        client = MockClient([(MockResponse(400), MOCK_CONTENT)])
        with pytest.raises(SystemExit, match='server communication error: status code=400, request id=REQ_ID'):
            client.post('/endpoint', {})

    def test_switch_api_url_for_connection_problems(self):
        client = MockClient([
            IOError('unable to reach server'),
            (MockResponse(500), MOCK_CONTENT),
            IOError('unable to reach server'),
            (MockResponse(200), MOCK_CONTENT),
        ])
        client.post('/endpoint', {})
        assert client.requests[0]['url'] != client.requests[1]['url']  # switch URL for connection issue
        assert client.requests[1]['url'] == client.requests[2]['url']  # keep URL for API error
        assert client.requests[2]['url'] != client.requests[3]['url']  # switch again for connection issue

    def test_give_up_when_persistent_server_error(self):
        client = MockClient([
            (MockResponse(500), MOCK_CONTENT),
            (MockResponse(500), MOCK_CONTENT),
            (MockResponse(500), MOCK_CONTENT),
            (MockResponse(500), MOCK_CONTENT),
        ])

        with pytest.raises(SystemExit, match='server communication error: status code=500, request id=REQ_ID'):
            client.post('/endpoint', {})

    def test_give_up_when_persistent_connection_error(self):
        client = MockClient([
            IOError('unable to reach server'),
            IOError('unable to reach server'),
            IOError('unable to reach server'),
            IOError('unable to reach server'),
        ])

        with pytest.raises(SystemExit, match='server communication error: unable to reach server'):
            client.post('/endpoint', {})


class MockClient(Client):
    def __init__(self, responses):
        super().__init__(MockSettings({
            'api_key': 'API_KEY',
            'api_retries': '3',
            'api_retry_cap': '0',
            'api_timeout': '0',
            'api_urls': ['API_URL'],
            'build_id': 'ID',
        }))
        self.responses = responses
        self.requests = []

    def _do_request(self, url, headers, body, timeout):
        self.requests.append({'url': url, 'headers': headers, 'body': body})
        head, tail = self.responses[0], self.responses[1:]
        self.responses = tail
        if isinstance(head, Exception):
            raise head
        return head


class MockResponse():
    def __init__(self, status, data={
        'x-request-id': 'REQ_ID',
    }):
        self.status = status
        self.data = data

    def get(self, key):
        return self.data.get(key)

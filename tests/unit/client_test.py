import uuid
import logging
import collections

import pytest

from testandconquer.client import Client

from tests.mock.settings import MockSettings


MOCK_CONTENT = """{"message": "Hello world!"}"""
HttpResponse = collections.namedtuple('HttpResponse', 'status')


class TestClient():

    def test_send_successfully(self, caplog):
        client = MockClient([(200, MOCK_CONTENT)])

        res = client.post('/endpoint', {})

        assert res == {'message': 'Hello world!'}
        assert warn_messages(caplog) == []

    def test_retry_on_404(self):
        client = MockClient([
            (404, MOCK_CONTENT),
            (200, MOCK_CONTENT),
        ])

        res = client.post('/endpoint', {})

        assert res == {'message': 'Hello world!'}

    def test_do_not_retry_on_400(self, caplog, fakeuuid):
        client = MockClient([(400, MOCK_CONTENT)])

        with pytest.raises(Exception, match='Client Error'):
            client.post('/endpoint', {})

        assert warn_messages(caplog) == ['could not get successful response from server [path=/endpoint] [status=400] [request-id=random-uuid]: Client Error']

    def test_handle_invalid_json_message(self, caplog, fakeuuid):
        client = MockClient([(400, """{INVALID JSON}""")])

        with pytest.raises(Exception, match='an error occurred'):
            client.post('/endpoint', {})

        assert warn_messages(caplog) == ['could not get successful response from server [path=/endpoint] [status=400] [request-id=random-uuid]: an error occurred']

    def test_print_error_message_from_server(self, caplog, fakeuuid):
        client = MockClient([(400, """{"error": "a helpful error message"}""")])

        with pytest.raises(Exception, match='a helpful error message'):
            client.post('/endpoint', {})

        assert warn_messages(caplog) == ['could not get successful response from server [path=/endpoint] [status=400] [request-id=random-uuid]: a helpful error message']

    def test_switch_api_url_for_connection_problems(self):
        client = MockClient([
            IOError('unable to reach server'),
            (500, MOCK_CONTENT),
            IOError('unable to reach server'),
            (200, MOCK_CONTENT),
        ])

        client.post('/endpoint', {})

        assert client.requests[0]['url'] != client.requests[1]['url']  # switch URL for connection issue
        assert client.requests[1]['url'] == client.requests[2]['url']  # keep URL for API error
        assert client.requests[2]['url'] != client.requests[3]['url']  # switch again for connection issue

    def test_give_up_when_persistent_server_error(self, caplog, fakeuuid):
        client = MockClient([
            (500, MOCK_CONTENT),
            (500, MOCK_CONTENT),
            (500, MOCK_CONTENT),
            (500, MOCK_CONTENT),
        ])

        with pytest.raises(Exception, match='Server Error'):
            client.post('/endpoint', {})

        assert warn_messages(caplog) == 4 * ['could not get successful response from server [path=/endpoint] [status=500] [request-id=random-uuid]: Server Error']

    def test_give_up_when_persistent_connection_error(self, caplog, fakeuuid):
        client = MockClient([
            IOError('unable to reach server'),
            IOError('unable to reach server'),
            IOError('unable to reach server'),
            IOError('unable to reach server'),
        ])

        with pytest.raises(Exception, match='unable to reach server'):
            client.post('/endpoint', {})

        assert warn_messages(caplog) == 4 * ['could not get successful response from server [path=/endpoint] [status=0] [request-id=random-uuid]: unable to reach server']


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

    def _execute_request(self, method, url, headers, body, timeout):
        self.requests.append({'url': url, 'headers': headers, 'body': body})
        head, tail = self.responses[0], self.responses[1:]
        self.responses = tail
        if isinstance(head, Exception):
            raise head
        return HttpResponse(head[0]), head[1].encode('utf-8')


def warn_messages(caplog):
    return [x.message for x in caplog.records if x.levelno == logging.WARNING]


@pytest.fixture
def fakeuuid(mocker):
    mocker.patch.object(uuid, 'uuid4', return_value='random-uuid', autospec=True)

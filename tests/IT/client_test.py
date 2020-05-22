import uuid
import logging
import asyncio

import pytest
from tests.mock.settings import MockSettings
from tests.mock.server import MockServer
from tests import assert_received_eventually

from testandconquer.client import Client, MessageType


class TestClient():

    @pytest.mark.asyncio
    async def test_connection(self, caplog):
        async with Context() as (client, server, subscriber):
            while len(server.connections) == 0:
                await asyncio.sleep(0.01)
            (path, headers) = server.connections[0]
            assert path == '/?primary'
            assert headers['X-API-Key'] == 'some-api-key'
            assert headers['X-Client-Name'] == 'pytest-conquer'
            assert headers['X-Client-Version'] == '1.0'
            assert headers['X-Connection-Attempt'] == '1'
            assert headers['X-Connection-ID'] == server.connections[0][1]['X-Connection-ID']
            assert headers['X-Env'] == 'provider'
            assert headers['X-Message-Format'] == 'json'
            assert headers['X-Message-Num'] == '0'
        assert warn_messages(caplog) == []

    @pytest.mark.skip
    @pytest.mark.asyncio
    async def test_connection_when_server_shuts_down(self, caplog):
        async with Context() as (client, server, subscriber):
            await server.stop()
            assert client.connected is False
            await server.start()
            while client.connected is False:
                await asyncio.sleep(0.01)
        assert warn_messages(caplog) == ['server error [code: 503], will try to re-connect']

    @pytest.mark.asyncio
    async def test_connection_when_server_not_reachable(self, caplog):
        settings = {
            'api_retry_limit': '3',
            'api_wait_limit': '0',
            'api_domain': 'doesnot.exist:801',
            'api_domain_fallback': 'doesnot.exist:802',
        }
        self.client = Client(MockSettings(settings))
        await self.client.start()
        while self.client.connection_attempt < 4:
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.01)
        assert warn_messages(caplog) == 4 * ['lost socket connection, will try to re-connect']
        assert error_messages(caplog) == ['failed to connect to server']

    @pytest.mark.asyncio
    async def test_reconnect(self, caplog):
        async with Context() as (client, server, subscriber):
            await client.send(MessageType.Suite, 'some-payload')
            while len(server.connections) == 0:
                await asyncio.sleep(0.01)
            await server.restart()
            while len(server.connections) == 1:
                await asyncio.sleep(0.01)
            (path, headers) = server.connections[1]
            assert path == '/?fallback'  # different URL
            assert headers['X-Connection-Attempt'] == '2'
            assert headers['X-Message-Num'] == '1'
        assert warn_messages(caplog) == []

    @pytest.mark.asyncio
    async def test_send_message_successfully(self, caplog):
        async with Context() as (client, server, subscriber):
            await client.send(MessageType.Suite, 'some-payload')
            await assert_received_eventually(server, [
                (MessageType.Suite.value, 'some-payload'),
            ])
        assert warn_messages(caplog) == []

    @pytest.mark.asyncio
    async def test_receive_message_successfully(self, caplog):
        async with Context() as (client, server, subscriber):
            await server.send(MessageType.Suite, 'some-payload')
            await assert_received_eventually(subscriber, [
                (MessageType.Suite.value, 'some-payload'),
            ])
        assert warn_messages(caplog) == []

    def test_build_url(self):
        assert Client.to_url('domain.com', 'us') == 'wss://equilibrium-us.domain.com'


class Subscriber():
    def __init__(self):
        self.received = []

    async def on_server_message(self, message_type, payload):
        self.received.append((message_type, payload))


class Context():
    def __init__(self, settings={}):
        self.settings = settings

    async def __aenter__(self):
        # set up server
        self.server = MockServer()
        await self.server.start()

        # set up client
        self.settings['api_domain'] = self.server.url + '?primary'
        self.settings['api_domain_fallback'] = self.server.url + '?fallback'
        self.client = Client(MockSettings(self.settings))
        await self.client.start()

        # set up subscriber
        self.subscriber = Subscriber()
        self.client.subscribe(self.subscriber)

        return self.client, self.server, self.subscriber

    async def __aexit__(self, _type, _value, _traceback):
        try:
            await self.client.stop()
        except Exception as err:
            print(err)

        try:
            await self.server.stop()
        except Exception as err:
            print(err)


def warn_messages(caplog):
    return [x.message for x in caplog.records if x.levelno == logging.WARNING]


def error_messages(caplog):
    return [x.message for x in caplog.records if x.levelno == logging.ERROR]


@pytest.fixture
def fakeuuid(mocker):
    mocker.patch.object(uuid, 'uuid4', return_value='random-uuid', autospec=True)

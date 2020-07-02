import uuid
import asyncio
from datetime import datetime

import pytest
from unittest import mock
from tests.mock.settings import MockSettings
from tests.mock.server import MockServer
from tests import assert_received_eventually, error_messages, warn_messages

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
            assert headers['X-Message-Num-Client'] == '-1'
            assert headers['X-Message-Num-Server'] == '-1'
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

    @mock.patch('testandconquer.util.datetime')
    def test_connection_when_server_not_reachable(self, datetime_mock, caplog, event_loop):
        settings = {
            'api_retry_limit': '3',
            'api_wait_limit': '0',
            'api_domain': 'doesnot.exist:801',
            'api_domain_fallback': 'doesnot.exist:802',
        }
        self.client = Client(MockSettings(settings))

        with pytest.raises(SystemExit):
            datetime_mock.utcnow = mock.Mock(return_value=datetime(2000, 1, 1))
            event_loop.run_until_complete(self.client.start())
            event_loop.run_until_complete(asyncio.sleep(1))

        assert warn_messages(caplog) == [
            'lost socket connection, will try to re-connect',
            'lost socket connection, will try to re-connect',
            'lost socket connection, will try to re-connect',
            'lost socket connection, will try to re-connect',
        ]
        assert error_messages(caplog) == [
            '\n'
            '\n'
            '    '
            '================================================================================\n'
            '\n'
            '    [ERROR] [CONQUER] COULD NOT CONNECT:\n'
            '\n'
            '    Unable to connect to server, giving up.\n'
            '    Please try again and contact support if the error persists.\n'
            '\n'
            '    [Client-Name = pytest-conquer]\n'
            '    [Client-Version = 1.0]\n'
            '    [Connection-Attempt = 4]\n'
            '    [Connection-ID = ' + str(self.client.id) + ']\n'
            '    [Timestamp = 2000-01-01T00:00:00]\n'
            '\n'
            '    '
            '================================================================================\n'
            '\n',
        ]

    @pytest.mark.asyncio
    async def test_reconnect(self, caplog):
        async with Context() as (client, server, subscriber):
            await server.send(MessageType.Envs, 'some-payload')
            while len(server.connections) == 0:
                await asyncio.sleep(0.01)
            await server.restart()
            while len(server.connections) == 1:
                await asyncio.sleep(0.01)
            (path, headers) = server.connections[1]
            assert path == '/?fallback'  # different URL
            assert headers['X-Connection-Attempt'] == '2'
            assert headers['X-Message-Num-Client'] == '0'  # 1 client message for ack'ing the server message
            assert headers['X-Message-Num-Server'] == '0'  # 1 server message was acked
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
            await server.send(MessageType.Envs, 'some-payload')
            await assert_received_eventually(subscriber, [
                (MessageType.Envs.value, 'some-payload'),
            ])
        assert warn_messages(caplog) == []

    def test_build_url(self):
        assert Client.to_url('domain.com', 'us') == 'wss://equilibrium-us.domain.com'

    @pytest.mark.asyncio
    async def test_ack_message(self):
        async with Context() as (client, server, subscriber):
            await server.send(MessageType.Envs, 'some-payload')
            await assert_received_eventually(server, [
                (MessageType.Ack.value, {'message_num': 0, 'status': 'success'}),
            ])

    @pytest.mark.asyncio
    async def test_dedup_message(self):
        async with Context() as (client, server, subscriber):
            await server.send(MessageType.Envs, 'some-payload')
            await assert_received_eventually(server, [
                (MessageType.Ack.value, {'message_num': 0, 'status': 'success'}),
            ])

            server.message_num = 0      # reset numbering to replicate duplicated message
            client.subscribers = None   # invalidate subscribers to make sure they aren't called

            await server.send(MessageType.Envs, 'some-payload')
            await assert_received_eventually(server, [
                (MessageType.Ack.value, {'message_num': 0, 'status': 'duplicate'}),
            ])

    @pytest.mark.asyncio
    async def test_out_of_order_message(self):
        async with Context() as (client, server, subscriber):
            server.message_num = 10     # pretend we're out of order
            client.subscribers = None   # invalidate subscribers to make sure they aren't called

            await server.send(MessageType.Envs, 'some-payload')
            await assert_received_eventually(server, [
                (MessageType.Ack.value, {'message_num': 10, 'status': 'out-of-order'}),
            ])

    @pytest.mark.asyncio
    async def test_never_skip_out_of_order_error_message(self):
        async with Context() as (client, server, subscriber):
            server.message_num = 10     # pretend we're out of order

            await server.send(MessageType.Error, 'some-payload')
            await assert_received_eventually(server, [
                (MessageType.Ack.value, {'message_num': 10, 'status': 'success'}),
            ])


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


@pytest.fixture
def fakeuuid(mocker):
    mocker.patch.object(uuid, 'uuid4', return_value='random-uuid', autospec=True)

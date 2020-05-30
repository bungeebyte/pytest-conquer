import json
import asyncio
import socket
import uuid
import time
from datetime import datetime
from enum import Enum

from testandconquer.util import system_exit
from testandconquer.vendor import websockets
from testandconquer import logger


class MessageType(Enum):
    Config = 'config'
    Done = 'done'
    Env = 'env'
    Error = 'error'
    Report = 'report'
    Schedule = 'schedule'
    Suite = 'suite'


class Client():

    def __init__(self, settings):
        self.id = uuid.uuid4()
        self.daemon = True
        self.stopping = False
        self.connected = False
        self.subscribers = []
        self.handle_task = None
        self.message_num = 0
        self.producer_task = None
        self.consumer_task = None
        self.connection_attempt = 0
        self.outgoing = asyncio.Queue()
        self.update_settings(settings)

    def update_settings(self, settings):
        self.api_key = settings.api_key
        self.api_retry_limit = settings.api_retry_limit
        self.api_wait_limit = settings.api_wait_limit
        self.api_urls = [
            Client.to_url(settings.api_domain, settings.api_region),
            Client.to_url(settings.api_domain_fallback, settings.api_region),
        ]
        self.client_name = settings.client_name
        self.client_version = settings.client_version
        self.system_provider = settings.system_provider

    @staticmethod
    def encode(message_num, message_type, payload):
        return json.dumps({
            'id': str(uuid.uuid4()),
            'num': str(message_num),
            'date': datetime.utcnow().isoformat(),
            'type': message_type.value,
            'payload': payload,
        })

    @staticmethod
    def decode(raw_message):
        return json.loads(raw_message)

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

    async def start(self):
        logger.debug('client: starting')
        self.handle_task = asyncio.ensure_future(self._handle())

    async def stop(self):
        logger.debug('client: shutting down')
        # quiescent the client
        self.stopping = True
        # wait for message queue to empty first
        await asyncio.wait_for(self.outgoing.join(), timeout=10)
        # now cancel all pending tasks
        if (self.consumer_task):
            self.consumer_task.cancel()
        if (self.producer_task):
            self.producer_task.cancel()
        if (self.handle_task):
            self.handle_task.cancel()

    async def send(self, message_type, payload):
        if self.stopping:
            logger.debug('client: not sending %s since shutting down'. message_type)
            return
        self.message_num += 1
        message = Client.encode(self.message_num, message_type, payload)
        await self.outgoing.put(message)

    async def _handle(self):
        try:
            async def consumer_handler(ws):
                try:
                    async for raw_message in ws:
                        message = Client.decode(raw_message)
                        for subscriber in self.subscribers:
                            resp = await subscriber.on_server_message(message['type'].lower(), message['payload'])
                            if resp is not None:
                                message_type, payload = resp
                                await self.send(message_type, payload)
                except asyncio.CancelledError:
                    pass  # we are shutting down

            async def producer_handler(ws):
                try:
                    while True:
                        message = await self.outgoing.get()  # blocks forever until something is available
                        await ws.send(message)
                        self.outgoing.task_done()
                except asyncio.CancelledError:
                    pass  # we are shutting down

            wait_before_reconnect = 0
            self.connection_attempt = 1

            while not self.stopping:
                url = self.api_urls[0]
                logger.debug('connecting to %s', url)
                headers = [
                    ('X-Api-Key', str(self.api_key)),
                    ('X-Client-Name', str(self.client_name)),
                    ('X-Client-Version', str(self.client_version)),
                    ('X-Connection-Attempt', str(self.connection_attempt)),
                    ('X-Connection-ID', str(self.id)),
                    ('X-Message-Num', str(self.message_num)),
                    ('X-Message-Format', 'json'),
                ]

                if self.system_provider:
                    headers.append(('X-Env', str(self.system_provider)))

                if wait_before_reconnect > 0:
                    logger.debug('retrying in %ss', wait_before_reconnect)
                    await asyncio.sleep(min(self.api_wait_limit, wait_before_reconnect))

                try:
                    start = time.time()
                    async with websockets.connect(
                        url,
                        ping_interval=None,     # don't send ping, that's the server's responsibility
                        max_size=None,          # accept any message size
                        max_queue=None,         # never drop a message
                        extra_headers=headers,
                    ) as ws:
                        self.connected = True
                        self.connection_attempt = 1

                        # run consumer and producer in parallel
                        self.consumer_task = asyncio.ensure_future(consumer_handler(ws))
                        self.producer_task = asyncio.ensure_future(producer_handler(ws))
                        done, pending = await asyncio.wait([self.producer_task, self.consumer_task], return_when=asyncio.FIRST_COMPLETED)

                        # re-raise any exceptions
                        for task in done:
                            err = task.exception()
                            if err:
                                logger.debug(err)
                                raise err

                        # one of them finished, let's cancel the other
                        for task in pending:
                            task.cancel()
                except websockets.exceptions.InvalidStatusCode as err:
                    logger.debug(err)
                    logger.warning('server error [code: %s], will try to re-connect' % err.status_code)
                except websockets.exceptions.ConnectionClosed as err:
                    logger.debug(err)
                    logger.warning('connection closed, will try to re-connect')
                except socket.gaierror as err:
                    logger.debug(err)
                    logger.warning('lost socket connection, will try to re-connect')
                except ConnectionRefusedError as err:
                    logger.debug(err)
                    logger.warning('connection refused, will try to re-connect')
                except OSError as err:
                    logger.debug(err)
                    logger.warning('connection error, will try to re-connect')
                finally:
                    self.connected = False
                    if self.connection_attempt > self.api_retry_limit:
                        self._abort()
                    self.connection_attempt += 1
                    wait_before_reconnect = 2 ** self.connection_attempt - (time.time() - start)
                    self.api_urls.reverse()  # we'll try the other URL next
        except asyncio.CancelledError:
            pass
        except Exception as err:
            logger.exception(err)

    def _abort(self):
        system_exit(
            'COULD NOT CONNECT:',
            'Unable to connect to server, giving up.\n'
            + 'Please try again and contact support if the error persists.',
            {
                'Client-Name': self.client_name,
                'Client-Version': self.client_version,
                'Connection-Attempt': self.connection_attempt,
                'Connection-ID': self.id,
            })

    @staticmethod
    def to_url(domain, region):
        if domain.startswith('localhost') or domain.startswith('0.0.0.0'):  # for testing
            return 'ws://' + domain
        return 'wss://equilibrium-' + region + '.' + domain

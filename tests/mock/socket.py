# import asyncio
# import queue

# from testandconquer.client import Client


# class MockWebsocketConnection:
#     def __init__(self):
#         self.received = queue.Queue()
#         self.outgoing = asyncio.Queue()

#     def __aiter__(self):
#         return self

#     async def __anext__(self):
#         while self.outgoing.empty:
#             pass
#             # print('next')
#         print('next!')
#         return await self.outgoing.get()

#     async def close(self):
#         await self.outgoing.join()

#     async def send(self, message):
#         self.received.put(Client.decode(message))


# class MockWebsocket:
#     def __init__(self):
#         self.connection = MockWebsocketConnection()

#     def __call__(self, url):
#         return self

#     # open async context manager
#     async def __aenter__(self, *args, **kwargs):
#         return self.connection

#     # close async context manager
#     async def __aexit__(self, *args, **kwargs):
#         self.connection.close()

#     # send message TO client
#     async def send(self, message_type, payload):
#         print('send')
#         self.connection.outgoing.put(Client.encode(message_type, payload))
#         print('sent')

#     def flush(self):
#         self.connection.outgoing.join()

#     @property
#     def received_messages(self):
#         return list(self.connection.received.queue)

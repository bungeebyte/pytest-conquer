import pytest

from tests.mock.server import MockServer


@pytest.yield_fixture()
async def mock_server(request):
    server = MockServer()
    await server.start()
    yield server
    await server.stop()

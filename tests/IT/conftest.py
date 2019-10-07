import pytest

from tests.mock.server import Server


@pytest.fixture()
def mock_server(request):
    server = Server()
    server.start()
    request.addfinalizer(server.stop)
    return server

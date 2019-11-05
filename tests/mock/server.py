import json
import threading
import zlib

from werkzeug.serving import make_server
from werkzeug.wrappers import Response, Request


class Server(threading.Thread):
    def __init__(self, host='0.0.0.0', port=0, **kwargs):
        self._server = make_server(host, port, self, **kwargs)
        self.requests = []
        self.responses = []
        super(Server, self).__init__(
            name=self.__class__,
            target=self._server.serve_forever)

    def __del__(self):
        self.stop()

    def __call__(self, environ, start_response):
        request = Request(environ)
        data = None
        path = request.path
        if path == '/heartbeat':
            return Response(status=200)(environ, start_response)
        if request.data:
            data = json.loads(zlib.decompress(request.data).decode('utf-8'))
        headers = dict([h for h in request.headers if h[0] != 'Content-Length'])
        self.requests.append((request.method, path, headers, data))
        if not self.responses:
            raise RuntimeError('no response defined')
        next_response = self.responses[0]
        self.responses = self.responses[1:]
        return next_response(environ, start_response)

    def stop(self):
        self._server.shutdown()

    def next_response(self, status, body):
        response = Response(status=status)
        if status != 502:
            response.headers = {
                'content-type': 'application/json',
                'x-request-id': '<unique-request-id>',
            }
        response.data = json.dumps(body)
        self.responses.append(response)

    @property
    def url(self):
        host, port = self._server.server_address
        return 'http://%s:%i' % (host, port)

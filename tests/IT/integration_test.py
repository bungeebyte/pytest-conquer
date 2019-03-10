import platform
import random
import string
import sys
import uuid
from collections import namedtuple

import psutil
import pytest

from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.scheduler import Scheduler
from maketestsgofaster.cloud.settings import Settings
from maketestsgofaster.model import Failure, Location

from tests.IT.server import Server


@pytest.mark.e2e
def test_successful_server_communication(config, server):
    settings = Settings(Env.create({
        'api_key': '42',
        'api_url': server.url,
        'build_dir': '/app',
        'build_id': config['build']['id'],
        'build_job': 'job',
        'vcs_branch': 'master',
        'vcs_repo': 'github.com/myrepo',
        'vcs_revision': 'asd43da',
        'vcs_revision_message': 'my commit',
    }))
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Authorization': '42',
        'Content-Encoding': 'gzip',
        'Content-Type': 'application/json; charset=UTF-8',
        'Host': server.url.replace('http://', ''),
        'User-Agent': 'python-official/1.0',
        'X-Attempt': '0',
        'X-Build-Id': config['build']['id'],
        'X-Build-Worker': 'build-worker',
    }
    scheduler = Scheduler(settings)

    # Round 0: collect tests

    scheduler.collect('test', Location('tests/IT/example_A.py', 'test_A', None))
    scheduler.collect('test', Location('tests/IT/example_B.py', 'test_B_1', None))
    scheduler.collect('test', Location('tests/IT/example_B.py', 'test_B_2', None))
    scheduler.collect('test', Location('tests/IT/example_C.py', 'test_C', None))

    # Round 1: init schedule

    server.next_response(200, {
        'items': [
            {'file': 'tests/IT/example_A.py', 'name': 'test_A'},
        ]})

    assert scheduler.next_file() == 'tests/IT/example_A.py'
    assert server.last_requests == [('POST', '/suites', headers, {
        'config': config,
        'items': [{
            'type': 'test',
            'file': 'tests/IT/example_A.py',
            'file_size': 0,
            'name': 'test_A',
            'line': None,
            'deps': [],
        }, {
            'type': 'test',
            'file': 'tests/IT/example_B.py',
            'file_size': 0,
            'name': 'test_B_1',
            'line': None,
            'deps': [],
        }, {
            'type': 'test',
            'file': 'tests/IT/example_B.py',
            'file_size': 0,
            'name': 'test_B_2',
            'line': None,
            'deps': [],
        }, {
            'type': 'test',
            'file': 'tests/IT/example_C.py',
            'file_size': 0,
            'name': 'test_C',
            'line': None,
            'deps': [],
        }],
    })]

    # Round 2: send report and receive next schedule items

    scheduler.report('test', Location('tests/IT/example_A.py', 'test_A', 3), 'failed', 0.2,
                     Failure('AssertionError', 'assert 1 + 1 == 4'))

    server.next_response(200, {
        'items': [
            {'file': 'tests/IT/example_B.py', 'name': 'test_B_1'},
            {'file': 'tests/IT/example_B.py', 'name': 'test_B_2'},
            {'file': 'tests/IT/example_C.py', 'name': 'test_C'},
        ]})

    assert scheduler.next_file() == 'tests/IT/example_B.py'
    assert scheduler.next_file() == 'tests/IT/example_C.py'

    assert server.last_requests == [('POST', '/reports', headers, {
        'config': config,
        'items': [{
            'file': 'tests/IT/example_A.py',
            'type': 'test',
            'name': 'test_A',
            'line': 3,
            'details': {
                'type': 'AssertionError',
                'message': 'assert 1 + 1 == 4',
            },
            'status': 'failed',
            'time': 0.2,
        }],
    })]

    scheduler.report('test', Location('tests/IT/example_B.py', 'test_B_1', 1), 'passed', 0.1, None)
    scheduler.report('test', Location('tests/IT/example_B.py', 'test_B_2', 2), 'passed', 0.15, None)
    scheduler.report('test', Location('tests/IT/example_C.py', 'test_C', 4), 'skipped', 0.01, None)

    # Round 3: send report and receive end

    server.next_response(200, {'items': []})

    assert scheduler.next_file() is None
    assert server.last_requests == [('POST', '/reports', headers, {
        'config': config,
        'items': [
            {
                'file': 'tests/IT/example_B.py',
                'type': 'test',
                'name': 'test_B_1',
                'line': 1,
                'status': 'passed',
                'time': 0.1,
            }, {
                'file': 'tests/IT/example_B.py',
                'type': 'test',
                'name': 'test_B_2',
                'line': 2,
                'status': 'passed',
                'time': 0.15,
            }, {
                'file': 'tests/IT/example_C.py',
                'type': 'test',
                'name': 'test_C',
                'line': 4,
                'status': 'skipped',
                'time': 0.01,
            },
        ],
    })]


@pytest.mark.e2e
def test_retry_on_server_error(config, server):
    settings = Settings(Env.create({
        'api_key': '42',
        'api_retry_cap': '0.1',
        'api_timeout': '0.1',
        'api_url': server.url,
        'build_id': '4242',
        'vcs_branch': 'master',
        'vcs_revision': 'asd43da',
    }))
    scheduler = Scheduler(settings)
    scheduler.collect('test', Location('tests/IT/example_A.py', 'test_A', None))

    server.next_response(500, {})
    server.next_response(500, {})
    server.next_response(200, {'items': [{'file': 'tests/IT/example_A.py', 'name': 'test_A'}]})

    resp = scheduler.next_file()
    assert resp == 'tests/IT/example_A.py'

    reqs = server.last_requests
    assert len(reqs) == 3
    assert [r[2]['X-Attempt'] for r in reqs] == ['0', '1', '2']


@pytest.mark.e2e
def test_give_up_when_receiving_400s_from_server(config, server):
    with pytest.raises(RuntimeError, match='server communication error - status code: 400, request id: <unique-request-id>'):
        settings = Settings(Env.create({
            'api_key': '42',
            'api_retry_cap': '0.1',
            'api_timeout': '0.1',
            'api_url': server.url,
            'build_id': '4242',
            'vcs_branch': 'master',
            'vcs_revision': 'asd43da',
        }))

        server.next_response(400, {})

        scheduler = Scheduler(settings)
        scheduler.next_file()


@pytest.mark.e2e
def test_give_up_when_server_unreachable(config):
    with pytest.raises(RuntimeError, match='server communication error - (.*) Connection refused'):
        settings = Settings(Env.create({
            'api_key': '42',
            'api_retries': '2',
            'api_retry_cap': '0.1',
            'api_timeout': '0.1',
            'api_url': 'http://localhost:12345',
            'build_id': '4242',
            'vcs_branch': 'master',
            'vcs_revision': 'asd43da',
        }))
        scheduler = Scheduler(settings)
        scheduler.next_file()


@pytest.mark.e2e
def test_stop_on_empty_schedule(config, server):
    settings = Settings(Env.create({
        'api_key': '42',
        'api_url': server.url,
        'build_id': '4242',
        'vcs_branch': 'master',
        'vcs_revision': 'asd43da',
    }))
    scheduler = Scheduler(settings)
    scheduler.collect('test', Location('tests/IT/example_A.py', 'test_A', None))

    server.next_response(200, {'items': []})

    assert scheduler.next_file() is None
    assert scheduler.next_file() is None  # again, just to be sure

    reqs = server.last_requests
    assert len(reqs) == 1


@pytest.fixture
def server(request):
    server = Server()
    server.start()
    request.addfinalizer(server.stop)
    return server


@pytest.fixture
def config(mocker):
    mocker.patch.object(psutil, 'cpu_count', return_value=3, autospec=True)
    mem = namedtuple('svmem', ['total', 'available', 'percent', 'used', 'free'])
    mocker.patch.object(psutil, 'virtual_memory', return_value=mem(17179869184, 0, 0, 0, 0), autospec=True)
    mocker.patch.object(platform, 'python_version', return_value='3.6', autospec=True)
    mocker.patch.object(platform, 'release', return_value='1.42', autospec=True)
    mocker.patch.object(platform, 'system', return_value='Linux', autospec=True)
    mocker.patch.object(uuid, 'uuid4', return_value='build-worker', autospec=True)
    mocker.patch.object(sys, 'argv', ['arg1'])
    build_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    return {
        'build': {'dir': '/app', 'id': build_id, 'job': 'job', 'pool': 0, 'project': None, 'url': None, 'worker': 'build-worker'},
        'client': {'capabilities': [], 'name': 'python-official', 'version': '1.0'},
        'platform': {'name': 'python', 'version': '3.6'},
        'runner': {'args': ['arg1'], 'name': None, 'plugins': [], 'root': None, 'version': None},
        'system': {'context': {}, 'name': 'custom', 'os': {'name': 'Linux', 'version': '1.42'}, 'cpus': 3, 'ram': 17179869184},
        'vcs': {'branch': 'master', 'pr': None, 'repo': 'github.com/myrepo',
                'revision': 'asd43da', 'revision_message': 'my commit', 'tag': None, 'type': 'git'},
    }

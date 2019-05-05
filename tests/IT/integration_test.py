import platform
import random
import string
import sys
import uuid
from collections import namedtuple
from datetime import datetime, timezone

import psutil
import pytest

from testandconquer.env import Env
from testandconquer.scheduler import Scheduler
from testandconquer.model import Failure, Location, ReportItem, ScheduleItem, SuiteItem, Tag

from tests.IT.mock.server import Server


time = datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)


@pytest.mark.e2e
def test_successful_server_communication(config, server):
    server.next_response(200, {})
    env = Env({
        'api_key': '42',
        'api_retries': '0',
        'api_retry_cap': '0',
        'api_timeout': '0',
        'api_url': server.url,
        'build_dir': '/app',
        'build_id': config['build']['id'],
        'build_job': 'job',
        'vcs_branch': 'master',
        'vcs_repo': 'github.com/myrepo',
        'vcs_revision': 'asd43da',
        'vcs_revision_message': 'my commit',
    })
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Authorization': '42',
        'Host': server.url.replace('http://', ''),
        'User-Agent': 'python-official/1.0',
        'X-Attempt': '0',
        'X-Build-Id': 'unknown',
        'X-Build-Node': 'unknown',
    }
    scheduler = Scheduler(env)

    assert server.last_requests == [('GET', '/envs', headers, None)]

    # Round 1: init schedule

    headers['Content-Encoding'] = 'gzip'
    headers['Content-Type'] = 'application/json; charset=UTF-8'
    headers['X-Build-Id'] = config['build']['id']
    headers['X-Build-Node'] = 'build-node'

    server.next_response(200, {
        'items': [
            {'file': 'tests/IT/stub/stub_A.py'},
        ]})

    assert scheduler.init([
        SuiteItem('test', Location('tests/IT/stub/stub_A.py', 'stub_A', 'TestClass', 'test_A', 1)),
        SuiteItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B_1', 1), tags=[Tag('my_group', False)]),
        SuiteItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B_2', 2), tags=[Tag(999, True)]),
        SuiteItem('test', Location('tests/IT/stub/stub_C.py', 'stub_C', 'TestClass', 'test_C', 1), deps=[
            SuiteItem('fixture', Location('tests/IT/stub/stub_fixture.py', 'fixtures', 'FixtureClass', 'test_C', 0)),
        ]),
    ]).items == [
        ScheduleItem('tests/IT/stub/stub_A.py'),
    ]

    assert server.last_requests == [('POST', '/suites', headers, {
        'config': config,
        'items': [{
            'type': 'test',
            'file': 'tests/IT/stub/stub_A.py',
            'module': 'stub_A',
            'class': 'TestClass',
            'func': 'test_A',
            'line': 1,
        }, {
            'type': 'test',
            'file': 'tests/IT/stub/stub_B.py',
            'module': 'stub_B',
            'class': 'TestClass',
            'func': 'test_B_1',
            'line': 1,
            'tags': [{'group': 'my_group'}],
        }, {
            'type': 'test',
            'file': 'tests/IT/stub/stub_B.py',
            'module': 'stub_B',
            'class': 'TestClass',
            'func': 'test_B_2',
            'tags': [{'group': '999', 'singleton': True}],
            'line': 2,
        }, {
            'type': 'test',
            'file': 'tests/IT/stub/stub_C.py',
            'module': 'stub_C',
            'class': 'TestClass',
            'func': 'test_C',
            'line': 1,
            'deps': [{
                'class': 'FixtureClass',
                'file': 'tests/IT/stub/stub_fixture.py',
                'func': 'test_C',
                'line': 0,
                'module': 'fixtures',
                'type': 'fixture',
            }],
        }],
    })]

    # Round 2: send report and receive next schedule items

    server.next_response(200, {
        'items': [
            {'file': 'tests/IT/stub/stub_B.py'},
            {'file': 'tests/IT/stub/stub_C.py'},
        ]})

    assert scheduler.next([
        ReportItem('test', Location('tests/IT/stub/stub_A.py', 'stub_A', 'TestClass', 'test_A', 3), 'failed',
                   Failure('AssertionError', 'assert 1 + 1 == 4'), time, time, 'wid', 'pid'),
    ]).items == [
        ScheduleItem('tests/IT/stub/stub_B.py'),
        ScheduleItem('tests/IT/stub/stub_C.py'),
    ]

    assert server.last_requests == [('POST', '/reports', headers, {
        'config': config,
        'items': [{
            'file': 'tests/IT/stub/stub_A.py',
            'type': 'test',
            'module': 'stub_A',
            'class': 'TestClass',
            'func': 'test_A',
            'line': 3,
            'error': {
                'type': 'AssertionError',
                'message': 'assert 1 + 1 == 4',
            },
            'process_id': 'pid',
            'worker_id': 'wid',
            'status': 'failed',
            'started_at': '2000-01-01T00:00:00.000Z',
            'finished_at': '2000-01-01T00:00:00.000Z',
        }],
    })]

    # Round 3: send report and receive end

    server.next_response(200, {'items': []})

    assert scheduler.next([
        ReportItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B_1', 1), 'passed', None, time, time, 'wid', 'pid'),
        ReportItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B_2', 2), 'passed', None, time, time, 'wid', 'pid'),
        ReportItem('test', Location('tests/IT/stub/stub_C.py', 'stub_C', 'TestClass', 'test_C', 4), 'skipped', None, time, time, 'wid', 'pid'),
    ]).items == []
    assert server.last_requests == [('POST', '/reports', headers, {
        'config': config,
        'items': [
            {
                'file': 'tests/IT/stub/stub_B.py',
                'type': 'test',
                'module': 'stub_B',
                'class': 'TestClass',
                'func': 'test_B_1',
                'line': 1,
                'status': 'passed',
                'process_id': 'pid',
                'worker_id': 'wid',
                'started_at': '2000-01-01T00:00:00.000Z',
                'finished_at': '2000-01-01T00:00:00.000Z',
            }, {
                'file': 'tests/IT/stub/stub_B.py',
                'type': 'test',
                'module': 'stub_B',
                'class': 'TestClass',
                'func': 'test_B_2',
                'line': 2,
                'status': 'passed',
                'process_id': 'pid',
                'worker_id': 'wid',
                'started_at': '2000-01-01T00:00:00.000Z',
                'finished_at': '2000-01-01T00:00:00.000Z',
            }, {
                'file': 'tests/IT/stub/stub_C.py',
                'type': 'test',
                'module': 'stub_C',
                'class': 'TestClass',
                'func': 'test_C',
                'line': 4,
                'status': 'skipped',
                'process_id': 'pid',
                'worker_id': 'wid',
                'started_at': '2000-01-01T00:00:00.000Z',
                'finished_at': '2000-01-01T00:00:00.000Z',
            },
        ],
    })]


@pytest.mark.e2e
def test_retry_env_on_server_error(config, server):
    server.next_response(500, {})
    server.next_response(500, {})
    server.next_response(200, {})

    env = Env({
        'api_key': '42',
        'api_retry_cap': '0',
        'api_timeout': '0',
        'api_url': server.url,
        'build_id': '4242',
        'vcs_branch': 'master',
        'vcs_revision': 'asd43da',
    })
    Scheduler(env)

    reqs = server.last_requests
    assert len(reqs) == 3
    assert [r[2]['X-Attempt'] for r in reqs] == ['0', '1', '2']


@pytest.mark.e2e
def test_retry_init_on_server_error(config, server):
    server.next_response(200, {})
    env = Env({
        'api_key': '42',
        'api_retry_cap': '0',
        'api_timeout': '0',
        'api_url': server.url,
        'build_id': '4242',
        'vcs_branch': 'master',
        'vcs_revision': 'asd43da',
    })
    scheduler = Scheduler(env)

    server.next_response(500, {})
    server.next_response(500, {})
    server.next_response(200, {'items': [{'file': 'tests/IT/stub/stub_A.py'}]})

    assert scheduler.init([
        SuiteItem('test', Location('tests/IT/stub/stub_A.py', 'stub_A', 'TestClass', 'test_A', None), '42', []),
    ]).items == [
        ScheduleItem('tests/IT/stub/stub_A.py'),
    ]

    reqs = server.last_requests
    assert len(reqs) == 4
    assert [r[2]['X-Attempt'] for r in reqs] == ['0', '0', '1', '2']


@pytest.mark.e2e
def test_give_up_when_receiving_400s_from_server(config, server):
    with pytest.raises(SystemExit, match='server communication error: status code=400, request id=<unique-request-id>'):
        env = Env({
            'api_key': '42',
            'api_retries': '0',
            'api_retry_cap': '0',
            'api_timeout': '0',
            'api_url': server.url,
            'build_id': '4242',
            'vcs_branch': 'master',
            'vcs_revision': 'asd43da',
        })

        server.next_response(400, {})

        scheduler = Scheduler(env)
        scheduler.init([])


@pytest.mark.e2e
def test_give_up_when_server_unreachable(config):
    with pytest.raises(SystemExit, match='server communication error: (.*) Connection refused'):
        env = Env({
            'api_key': '42',
            'api_retries': '2',
            'api_retry_cap': '0',
            'api_timeout': '0',
            'api_url': 'http://localhost:12345',
            'build_id': '4242',
            'vcs_branch': 'master',
            'vcs_revision': 'asd43da',
        })
        scheduler = Scheduler(env)
        scheduler.init([])


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
    mocker.patch.object(uuid, 'uuid4', return_value='build-node', autospec=True)
    mocker.patch.object(sys, 'argv', ['arg1'])
    build_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    return {
        'build': {'dir': '/app', 'id': build_id, 'job': 'job', 'pool': 0, 'project': None, 'url': None, 'node': 'build-node'},
        'client': {'capabilities': ['fixtures', 'isolated_process', 'lifecycle_timings', 'split_by_file'],
                   'name': 'python-official', 'version': '1.0', 'workers': 1},
        'platform': {'name': 'python', 'version': '3.6'},
        'runner': {'args': ['arg1'], 'name': None, 'plugins': [], 'root': None, 'version': None},
        'system': {'context': {}, 'provider': 'custom', 'os': 'Linux', 'os_version': '1.42', 'cpus': 3, 'ram': 17179869184},
        'vcs': {'branch': 'master', 'pr': None, 'repo': 'github.com/myrepo',
                'revision': 'asd43da', 'revision_message': 'my commit', 'tag': None, 'type': 'git'},
    }

import platform
import random
import string
import sys
import uuid
import asyncio
import os
from collections import namedtuple
from datetime import datetime, timezone

import psutil
import pytest

from testandconquer.client import Client, MessageType
from testandconquer.scheduler import Scheduler
from testandconquer.model import Failure, Location, Report, ReportItem, ScheduleBatch, ScheduleItem, Schedule, SuiteItem, Tag

from tests.mock.settings import MockSettings
from tests import assert_received_eventually


time = datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio()
async def test_successful_server_communication(config, mock_server):
    os.environ['MY_CI'] = 'true'
    settings = MockSettings({
        'api_domain': mock_server.url,
        'api_key': 'api_key',
        'api_retries': '0',
        'api_retry_cap': '0',
        'api_timeout': '1',
        'build_dir': '/app',
        'build_id': config['build']['id'],
        'build_job': 'job',
        'enabled': True,
        'vcs_branch': 'master',
        'vcs_repo': 'github.com/myrepo',
        'vcs_revision': 'asd43da',
        'vcs_revision_message': 'my commit',
    })
    client = Client(settings)
    client.subscribe(settings)
    suite_items = [
        SuiteItem('test', Location('tests/IT/stub/stub_A.py', 'stub_A', 'TestClass', 'test_A', 1)),
        SuiteItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B', 1), tags=[Tag('my_group', False)]),
        SuiteItem('test', Location('tests/IT/stub/stub_C.py', 'stub_C', 'TestClass', 'test_C', 1), deps=[
            SuiteItem('fixture', Location('tests/IT/stub/stub_fixture.py', 'fixtures', 'FixtureClass', 'test_C', 0)),
        ]),
    ]
    scheduler = Scheduler(settings, client, suite_items, 'my_worker_id')

    # (1) CONNECT

    await client.start()

    # (2) SERVER REQUESTS ENV

    await mock_server.send(MessageType.Env, [{'name': 'CI', 'conditions': ['my_CI'], 'mapping': {}}])

    # (3) CLIENT REPLIES WITH ENV

    await assert_received_eventually(mock_server, [
        (MessageType.Env.value, 'CI'),
    ])

    # (4) SERVER REQUESTS CONFIG

    await mock_server.send(MessageType.Config, {})

    # (5) CLIENT REPLIES WITH CONFIG

    await assert_received_eventually(mock_server, [
        (MessageType.Config.value, {
            'build': {'dir': '/app', 'id': config['build']['id'], 'job': 'job', 'node': 'random-uuid', 'pool': 0, 'project': None, 'url': None},
            'client': {
                'capabilities': ['fixtures', 'lifecycle_timings', 'split_by_file'],
                'messages': ['config', 'done', 'env', 'error', 'report', 'schedule', 'suite'],
                'name': 'pytest-conquer', 'version': '1.0', 'workers': 1, 'worker_id': 'my_worker_id',
            },
            'platform': {'name': 'python', 'version': '3.6'},
            'runner': {'args': ['arg1'], 'name': None, 'plugins': [], 'root': None, 'version': None},
            'system': {'context': {}, 'cpus': 3, 'os': 'Linux', 'os_version': '1.42', 'provider': 'CI', 'ram': 17179869184},
            'vcs': {'branch': 'master', 'pr': None, 'repo': 'github.com/myrepo', 'revision': 'asd43da', 'revision_message': 'my commit', 'tag': None, 'type': 'git'},
        }),
    ])

    # (6) SERVER REQUESTS SUITE

    await mock_server.send(MessageType.Suite, {})

    # (7) CLIENT SENDS SUITE

    await assert_received_eventually(mock_server, [
        (MessageType.Suite.value, {
            'items': [
                {'type': 'test', 'location': {'file': 'tests/IT/stub/stub_A.py', 'func': 'test_A', 'module': 'stub_A', 'class': 'TestClass', 'line': 1}},
                {'type': 'test', 'location': {'file': 'tests/IT/stub/stub_B.py', 'func': 'test_B', 'module': 'stub_B', 'class': 'TestClass', 'line': 1}, 'tags': [{'group': 'my_group'}]},
                {'type': 'test', 'location': {'file': 'tests/IT/stub/stub_C.py', 'func': 'test_C', 'module': 'stub_C', 'class': 'TestClass', 'line': 1},
                    'deps': [{'type': 'fixture', 'location': {'file': 'tests/IT/stub/stub_fixture.py', 'func': 'test_C', 'module': 'fixtures', 'class': 'FixtureClass'}}]},
            ],
        }),
    ])

    # (8) SERVER SENDS SCHEDULE #1

    await mock_server.send(MessageType.Schedule, {
        'batches': [{
            'items': [{'file': 'tests/IT/stub/stub_A.py'}],
        }, {
            'items': [{'file': 'tests/IT/stub/stub_B.py'}],
        }],
    })

    assert await scheduler.next() == Schedule([
        ScheduleBatch([ScheduleItem('tests/IT/stub/stub_A.py')]),
        ScheduleBatch([ScheduleItem('tests/IT/stub/stub_B.py')]),
    ])

    # (9) CLIENT SENDS REPORT #1

    await scheduler.report(Report([
        ReportItem('test', Location('tests/IT/stub/stub_A.py', 'stub_A', 'TestClass', 'test_A', 3), 'failed',
                   Failure('AssertionError', 'assert 1 + 1 == 4'), time, time),
    ], time, time, time))

    await assert_received_eventually(mock_server, [
        (MessageType.Report.value, {
            'items': [{
                'type': 'test',
                'location': {'file': 'tests/IT/stub/stub_A.py', 'func': 'test_A', 'module': 'stub_A', 'class': 'TestClass', 'line': 3},
                'status': 'failed',
                'started_at': '2000-01-01T00:00:00.000Z',
                'finished_at': '2000-01-01T00:00:00.000Z',
                'error': {'type': 'AssertionError', 'message': 'assert 1 + 1 == 4'},
            }],
            'started_at': '2000-01-01T00:00:00.000Z',
            'finished_at': '2000-01-01T00:00:00.000Z',
        }),
    ])

    # (10) SERVER SENDS SCHEDULE #2

    await mock_server.send(MessageType.Schedule, {
        'batches': [{
            'items': [{'file': 'tests/IT/stub/stub_C.py'}],
        }],
    })

    assert await scheduler.next() == Schedule([
        ScheduleBatch([ScheduleItem('tests/IT/stub/stub_C.py')]),
    ])

    # (11) CLIENT SENDS REPORT #2

    await scheduler.report(Report([
        ReportItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B', 1), 'passed', None, time, time),
    ], time, time, time))

    await assert_received_eventually(mock_server, [
        (MessageType.Report.value, {
            'items': [{
                'type': 'test',
                'location': {'file': 'tests/IT/stub/stub_B.py', 'func': 'test_B', 'module': 'stub_B', 'class': 'TestClass', 'line': 1},
                'status': 'passed',
                'started_at': '2000-01-01T00:00:00.000Z',
                'finished_at': '2000-01-01T00:00:00.000Z',
            }],
            'started_at': '2000-01-01T00:00:00.000Z',
            'finished_at': '2000-01-01T00:00:00.000Z',
        }),
    ])

    # (12) CLIENT SENDS REPORT #3

    await scheduler.report(Report([
        ReportItem('test', Location('tests/IT/stub/stub_C.py', 'stub_C', 'TestClass', 'test_C', 1), 'passed', None, time, time),
    ], time, time, time))

    await assert_received_eventually(mock_server, [
        (MessageType.Report.value, {
            'items': [{
                'type': 'test',
                'location': {'file': 'tests/IT/stub/stub_C.py', 'func': 'test_C', 'module': 'stub_C', 'class': 'TestClass', 'line': 1},
                'status': 'passed',
                'started_at': '2000-01-01T00:00:00.000Z',
                'finished_at': '2000-01-01T00:00:00.000Z',
            }],
            'started_at': '2000-01-01T00:00:00.000Z',
            'finished_at': '2000-01-01T00:00:00.000Z',
        }),
    ])

    # (13) SERVER SENDS DONE

    await mock_server.send(MessageType.Done, {})
    await asyncio.sleep(0.1)
    assert scheduler.more is False

    # (14) SHUTDOWN

    await scheduler.stop()
    await client.stop()


@pytest.fixture
def config(mocker):
    mocker.patch.object(psutil, 'cpu_count', return_value=3, autospec=True)
    mem = namedtuple('svmem', ['total', 'available', 'percent', 'used', 'free'])
    mocker.patch.object(psutil, 'virtual_memory', return_value=mem(17179869184, 0, 0, 0, 0), autospec=True)
    mocker.patch.object(platform, 'python_version', return_value='3.6', autospec=True)
    mocker.patch.object(platform, 'release', return_value='1.42', autospec=True)
    mocker.patch.object(platform, 'system', return_value='Linux', autospec=True)
    mocker.patch.object(uuid, 'uuid4', return_value='random-uuid', autospec=True)
    mocker.patch.object(sys, 'argv', ['arg1'])
    build_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    return {
        'build': {'dir': '/app', 'id': build_id, 'job': 'job', 'pool': 0, 'project': None, 'url': None, 'node': 'random-uuid'},
        'client': {'capabilities': ['heartbeat', 'fixtures', 'isolated_process', 'lifecycle_timings', 'split_by_file'],
                   'name': 'pytest-conquer', 'version': '1.0', 'workers': 1, 'worker_id': 'my_worker_id'},
        'platform': {'name': 'python', 'version': '3.6'},
        'runner': {'args': ['arg1'], 'name': None, 'plugins': [], 'root': None, 'version': None},
        'system': {'context': {}, 'provider': 'custom', 'os': 'Linux', 'os_version': '1.42', 'cpus': 3, 'ram': 17179869184},
        'vcs': {'branch': 'master', 'pr': None, 'repo': 'github.com/myrepo',
                'revision': 'asd43da', 'revision_message': 'my commit', 'tag': None, 'type': 'git'},
    }

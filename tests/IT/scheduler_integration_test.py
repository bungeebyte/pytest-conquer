import platform
import random
import string
import sys
import uuid
import re
import logging
import wsgiref.handlers
from collections import namedtuple
from datetime import datetime, timezone

import psutil
import pytest

from testandconquer.scheduler import Scheduler
from testandconquer.model import Failure, Location, ReportItem, ScheduleBatch, ScheduleItem, Schedule, SuiteItem, Tag

from tests.mock.settings import MockSettings


time = datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio()
@pytest.mark.wip()
async def test_successful_server_communication(config, mock_server):
    get_headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Authorization': 'api_key',
        'Date': 'Wed, 21 Oct 2015 07:28:00 GMT',
        'Host': mock_server.url.replace('http://', ''),
        'User-Agent': 'pytest-conquer/1.0',
        'X-Attempt': '0',
        'X-Build-Id': config['build']['id'],
        'X-Build-Node': 'random-uuid',
        'X-Request-Id': 'random-uuid',
    }
    post_headers = get_headers.copy()
    post_headers.update({
        'Content-Encoding': 'gzip',
        'Content-Type': 'application/json; charset=UTF-8',
    })

    scheduler = Scheduler(MockSettings({
        'api_key': 'api_key',
        'api_retries': '0',
        'api_retry_cap': '0',
        'api_timeout': '0',
        'api_url': mock_server.url,
        'build_dir': '/app',
        'build_id': config['build']['id'],
        'build_job': 'job',
        'enabled': True,
        'vcs_branch': 'master',
        'vcs_repo': 'github.com/myrepo',
        'vcs_revision': 'asd43da',
        'vcs_revision_message': 'my commit',
    }), 'my_worker_id')

    # Round 1

    mock_server.next_response(200, {
        'run_id': 'some_run_id',
        'job_id': 'some_job_id',
        'batches': [{
            'items': [{'file': 'tests/IT/stub/stub_A.py'}],
        }],
    })

    assert await scheduler.start([
        SuiteItem('test', Location('tests/IT/stub/stub_A.py', 'stub_A', 'TestClass', 'test_A', 1)),
        SuiteItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B_1', 1), tags=[Tag('my_group', False)]),
        SuiteItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B_2', 2), tags=[Tag(999, True)]),
        SuiteItem('test', Location('tests/IT/stub/stub_C.py', 'stub_C', 'TestClass', 'test_C', 1), deps=[
            SuiteItem('fixture', Location('tests/IT/stub/stub_fixture.py', 'fixtures', 'FixtureClass', 'test_C', 0)),
        ]),
    ]) == Schedule([
        ScheduleBatch([ScheduleItem('tests/IT/stub/stub_A.py')]),
    ])

    # Round 2

    mock_server.next_response(200, {
        'run_id': 'some_run_id',
        'job_id': 'some_job_id',
        'batches': [{
            'items': [{'file': 'tests/IT/stub/stub_B.py'}],
        }, {
            'items': [{'file': 'tests/IT/stub/stub_C.py'}],
        }],
    })

    assert await scheduler.next([
        ReportItem('test', Location('tests/IT/stub/stub_A.py', 'stub_A', 'TestClass', 'test_A', 3), 'failed',
                   Failure('AssertionError', 'assert 1 + 1 == 4'), time, time, 'pid'),
    ]) == Schedule([
        ScheduleBatch([ScheduleItem('tests/IT/stub/stub_B.py')]),
        ScheduleBatch([ScheduleItem('tests/IT/stub/stub_C.py')]),
    ])

    # Round 3

    mock_server.next_response(200, {
        'run_id': 'some_run_id',
        'job_id': 'some_job_id',
        'batches': [],
    })

    assert await scheduler.next([
        ReportItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B_1', 1), 'passed', None, time, time, 'pid'),
        ReportItem('test', Location('tests/IT/stub/stub_B.py', 'stub_B', 'TestClass', 'test_B_2', 2), 'failed', None, time, time, 'pid'),
        ReportItem('test', Location('tests/IT/stub/stub_C.py', 'stub_C', 'TestClass', 'test_C', 4), 'skipped', None, None, None, 'pid'),
    ]) == Schedule([])

    await scheduler.stop()

    # check schedules were transmitted correctly

    assert mock_server.requests == [
        ('POST', '/schedules', post_headers, {
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
        }),
        ('PUT', '/schedules', post_headers, {
            'run_id': 'some_run_id',
            'job_id': 'some_job_id',
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
                'status': 'failed',
                'started_at': '2000-01-01T00:00:00.000Z',
                'finished_at': '2000-01-01T00:00:00.000Z',
            }],
        }),
        ('PUT', '/schedules', post_headers, {
            'run_id': 'some_run_id',
            'job_id': 'some_job_id',
            'items': [{
                'file': 'tests/IT/stub/stub_B.py',
                'type': 'test',
                'module': 'stub_B',
                'class': 'TestClass',
                'func': 'test_B_1',
                'line': 1,
                'status': 'passed',
                'process_id': 'pid',
                'started_at': '2000-01-01T00:00:00.000Z',
                'finished_at': '2000-01-01T00:00:00.000Z',
            }, {
                'file': 'tests/IT/stub/stub_B.py',
                'type': 'test',
                'module': 'stub_B',
                'class': 'TestClass',
                'func': 'test_B_2',
                'line': 2,
                'status': 'failed',
                'process_id': 'pid',
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
            }],
        }),
    ]


@pytest.mark.asyncio()
@pytest.mark.wip()
async def test_retry_scheduling_on_server_error(config, mock_server, caplog):
    scheduler = Scheduler(MockSettings({
        'api_key': 'api_key',
        'api_retry_cap': '0',
        'api_timeout': '0',
        'api_url': mock_server.url,
        'build_id': 'build_id',
        'enabled': True,
        'vcs_branch': 'master',
        'vcs_revision': 'asd43da',
    }), 'my_worker_id')

    mock_server.next_response(500, {})
    mock_server.next_response(500, {})
    mock_server.next_response(200, {
        'run_id': 'some_run_id',
        'job_id': 'some_job_id',
        'batches': [{
            'items': [{'file': 'tests/IT/stub/stub_A.py'}],
        }]})

    assert await scheduler.start([
        SuiteItem('test', Location('tests/IT/stub/stub_A.py', 'stub_A', 'TestClass', 'test_A', None), 'api_key', []),
    ]) == Schedule([
        ScheduleBatch([ScheduleItem('tests/IT/stub/stub_A.py')]),
    ])
    await scheduler.stop()

    reqs = mock_server.requests
    assert len(reqs) == 3
    assert [r[2]['X-Attempt'] for r in reqs] == ['0', '1', '2']

    messages = [x.message for x in caplog.records if x.levelno == logging.WARNING]
    assert messages == 2 * ['could not get successful response from server [status=500] [request-id=random-uuid]: Server Error']


@pytest.mark.asyncio()
@pytest.mark.wip()
async def test_give_up_when_server_unreachable(config, caplog):
    with pytest.raises(SystemExit, match='EXIT: server communication error'):
        scheduler = Scheduler(MockSettings({
            'api_key': 'api_key',
            'api_retries': '2',
            'api_retry_cap': '0',
            'api_timeout': '0',
            'api_url': 'http://localhost:12345',
            'api_url_fallback': 'http://localhost:12345',
            'build_id': 'build_id',
            'enabled': True,
            'vcs_branch': 'master',
            'vcs_revision': 'asd43da',
        }), 'my_worker_id')
        await scheduler.start([])

    await scheduler.stop()

    messages = [x.message for x in caplog.records if x.levelno == logging.WARNING]
    assert re.match(r'could not get successful response from server \[status=0\] \[request-id=random-uuid\]: \[Errno [0-9]+\] Connection refused', messages[0])


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
    mocker.patch.object(wsgiref.handlers, 'format_date_time', return_value='Wed, 21 Oct 2015 07:28:00 GMT', autospec=True)
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

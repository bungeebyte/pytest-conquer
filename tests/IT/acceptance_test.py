# TBD: end-to-end with mock server

import os

import pytest

from tests.IT import run_test, assert_outcomes
from tests.mock.server import Server


@pytest.mark.wip()
def test_end_to_end(testdir, server):
    server.next_response(200, {
        'envs': {},
    })

    server.next_response(200, {
        'run_id': 'some_run_id',
        'job_id': 'some_job_id',
        'batches': [{
            'items': [{'file': 'fixtures/test_function_pass.py'}],
        }],
    })

    server.next_response(200, {
        'run_id': 'some_run_id',
        'job_id': 'some_job_id',
        'batches': [],
    })

    (result, scheduler) = run_test(testdir, ['fixtures/test_function_pass.py'])
    assert_outcomes(result, passed=1)

    assert len(server.requests) == 3


@pytest.fixture(scope='module', autouse=True)
def mock_settings(server):
    os.environ['CONQUER_API_URL'] = server.url
    os.environ['CONQUER_API_KEY'] = '<API-KEY>'
    os.environ['CONQUER_API_RETRIES'] = '0'
    os.environ['CONQUER_API_TIMEOUT'] = '0'
    os.environ['CONQUER_BUILD_ID'] = '<BUILD-ID>'
    os.environ['CONQUER_VCS_BRANCH'] = '<BRANCH>'
    os.environ['CONQUER_VCS_REVISION'] = '<BRANCH>'
    yield
    del os.environ['CONQUER_API_URL']
    del os.environ['CONQUER_API_KEY']
    del os.environ['CONQUER_API_RETRIES']
    del os.environ['CONQUER_API_TIMEOUT']
    del os.environ['CONQUER_BUILD_ID']
    del os.environ['CONQUER_VCS_BRANCH']
    del os.environ['CONQUER_VCS_REVISION']


@pytest.fixture(scope='module')
def server(request):
    server = Server()
    server.start()
    request.addfinalizer(server.stop)
    return server

import os

import pytest

from tests.IT import run_test, assert_outcomes


def test_end_to_end(testdir, mock_server):
    mock_server.next_response(200, {
        'envs': {},
    })

    mock_server.next_response(200, {
        'run_id': 'some_run_id',
        'job_id': 'some_job_id',
        'batches': [{
            'items': [{'file': 'fixtures/test_function_pass.py'}],
        }],
    })

    mock_server.next_response(200, {
        'run_id': 'some_run_id',
        'job_id': 'some_job_id',
        'batches': [],
    })

    (result, scheduler) = run_test(testdir, ['fixtures/test_function_pass.py'])
    assert_outcomes(result, passed=1)

    assert len(mock_server.requests) == 3


@pytest.fixture(autouse=True)
def mock_settings(mock_server):
    os.environ['CONQUER_API_URL'] = mock_server.url
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

from datetime import datetime

import pytest
from unittest import mock
from unittest.mock import patch, PropertyMock

from tests.mock.settings import MockSettings
from tests import error_messages


@patch('testandconquer.plugin.sys')
@patch('testandconquer.util.datetime')
def test_fails_for_old_python_version(datetime_mock, mock_sys, caplog):
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester
    type(mock_sys).version_info = PropertyMock(return_value=(3, 5))
    assert testandconquer.plugin.fatal_error is None
    datetime_mock.utcnow = mock.Mock(return_value=datetime(2000, 1, 1))
    testandconquer.plugin.pytest_configure(None)
    assert testandconquer.plugin.fatal_error is True
    assert error_messages(caplog) == [
        '\n'
        '\n'
        '    '
        '================================================================================\n'
        '\n'
        '    [ERROR] [CONQUER] COULD NOT START\n'
        '\n'
        '    Sorry, pytest-conquer requires at least Python 3.6.0.\n'
        '\n'
        '    [Timestamp = 2000-01-01T00:00:00]\n'
        '\n'
        '    '
        '================================================================================\n'
        '\n',
    ]
    testandconquer.plugin.fatal_error = None


@patch('testandconquer.util.datetime')
@patch.object(pytest, '__version__', '3.0.4')
def test_fails_for_old_pytest_version(datetime_mock, caplog):
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester
    assert testandconquer.plugin.fatal_error is None
    datetime_mock.utcnow = mock.Mock(return_value=datetime(2000, 1, 1))
    testandconquer.plugin.pytest_configure(None)
    assert testandconquer.plugin.fatal_error is True
    assert error_messages(caplog) == [
        '\n'
        '\n'
        '    '
        '================================================================================\n'
        '\n'
        '    [ERROR] [CONQUER] COULD NOT START\n'
        '\n'
        '    Sorry, pytest-conquer requires at least pytest 3.6.0.\n'
        '\n'
        '    [Timestamp = 2000-01-01T00:00:00]\n'
        '\n'
        '    '
        '================================================================================\n'
        '\n',
    ]
    testandconquer.plugin.fatal_error = None


@pytest.fixture(scope='module', autouse=True)
def mock_generate_settings():
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester
    previous = testandconquer.plugin.create_settings
    testandconquer.plugin.create_settings = lambda config: MockSettings({'enabled': True})
    yield  # run test
    testandconquer.plugin.create_settings = previous

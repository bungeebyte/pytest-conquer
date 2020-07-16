from datetime import datetime

import pytest
from unittest import mock
from unittest.mock import patch, Mock, PropertyMock

from tests import error_messages
from tests.mock.settings import MockSettings
from tests.mock.scheduler import MockScheduler


def test_skip_plugin_if_collectonly(config_mock):
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester

    config_mock.option.collectonly = True

    testandconquer.plugin.pytest_configure(config_mock)

    assert testandconquer.plugin.settings is None
    assert testandconquer.plugin.scheduler is None


def test_skip_plugin_if_not_enabled(config_mock):
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester

    config_mock.option.enabled = False

    testandconquer.plugin.pytest_configure(config_mock)

    assert testandconquer.plugin.scheduler is None


@patch('testandconquer.plugin.sys')
@patch('testandconquer.util.datetime')
def test_fails_for_old_python_version(datetime_mock, mock_sys, config_mock, caplog):
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester

    type(mock_sys).version_info = PropertyMock(return_value=(3, 5))
    datetime_mock.utcnow = mock.Mock(return_value=datetime(2000, 1, 1))

    assert testandconquer.plugin.fatal_error is None

    testandconquer.plugin.pytest_configure(config_mock)

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
def test_fails_for_old_pytest_version(datetime_mock, config_mock, caplog):
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester

    datetime_mock.utcnow = mock.Mock(return_value=datetime(2000, 1, 1))

    assert testandconquer.plugin.fatal_error is None

    testandconquer.plugin.pytest_configure(config_mock)

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


@pytest.fixture()
def config_mock():
    config_mock = Mock()
    config_mock.__Scheduler = MockScheduler
    config_mock.__Settings = MockSettings
    config_mock.option = type('option', (object,), dict(enabled=True, collectonly=False))
    config_mock.pluginmanager.list_plugin_distinfo.return_value = []
    return config_mock

import sys

import pytest
from unittest import mock
from unittest.mock import patch

import testandconquer.plugin
import testandconquer.settings
from testandconquer.scheduler import Scheduler

from tests.mock.settings import MockSettings


def test_fails_for_old_python_version():
    with mock.patch.object(sys, 'version_info') as version_mock:
        version_mock.major = 3
        version_mock.minor = 3
        with pytest.raises(SystemExit):
            testandconquer.plugin.pytest_configure(None)


@patch.object(pytest, '__version__', '3.0.4')
def test_fails_for_old_pytest_version():
    with pytest.raises(SystemExit):
        testandconquer.plugin.pytest_configure(None)


@pytest.fixture(scope='module', autouse=True)
def mock_generate_settings():
    previous = testandconquer.plugin.create_scheduler
    testandconquer.plugin.create_scheduler = lambda config: Scheduler(MockSettings({'enabled': True}))
    yield  # run test
    testandconquer.plugin.create_scheduler = previous

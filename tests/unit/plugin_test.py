import pytest
from unittest.mock import patch, PropertyMock

from tests.mock.settings import MockSettings


@patch('testandconquer.plugin.sys')
def test_fails_for_old_python_version(mock_sys):
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester
    type(mock_sys).version_info = PropertyMock(return_value=(3, 4))
    with pytest.raises(SystemExit):
        testandconquer.plugin.pytest_configure(None)


@patch.object(pytest, '__version__', '3.0.4')
def test_fails_for_old_pytest_version():
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester
    with pytest.raises(SystemExit):
        testandconquer.plugin.pytest_configure(None)


@pytest.fixture(scope='module', autouse=True)
def mock_generate_settings():
    import testandconquer.plugin  # has to be inline since the module can't be loaded upfront due to pytester
    previous = testandconquer.plugin.create_settings
    testandconquer.plugin.create_settings = lambda config: MockSettings({'enabled': True})
    yield  # run test
    testandconquer.plugin.create_settings = previous

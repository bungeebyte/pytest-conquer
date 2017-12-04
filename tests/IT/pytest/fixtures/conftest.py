import pytest


@pytest.fixture(scope='session')
def fixture_session():
    return 'session'

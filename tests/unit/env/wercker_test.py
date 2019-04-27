import os
import pytest

from testandconquer.env import Env
from testandconquer.env.wercker import Wercker


def test_create(wercker_env):
    env = Env.create()
    assert env.name() is 'wercker'
    assert type(env) is Wercker


def test_settings(wercker_env):
    env = Env.create()
    assert env.build_id() == 'build_started_at'
    assert env.build_url() == 'build_url'
    assert env.context() == {
        'WERCKER_APPLICATION_URL': 'app-url',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_revision() == 'sha'


@pytest.fixture()
def wercker_env():
    os.environ['CI'] = 'true'
    os.environ['WERCKER_APPLICATION_URL'] = 'app-url'
    os.environ['WERCKER_GIT_BRANCH'] = 'branch'
    os.environ['WERCKER_GIT_COMMIT'] = 'sha'
    os.environ['WERCKER_GIT_OWNER'] = 'org'
    os.environ['WERCKER_GIT_REPOSITORY'] = 'repo'
    os.environ['WERCKER_MAIN_PIPELINE_STARTED'] = 'build_started_at'
    os.environ['WERCKER_RUN_URL'] = 'build_url'
    yield
    del os.environ['CI']
    del os.environ['WERCKER_GIT_BRANCH']

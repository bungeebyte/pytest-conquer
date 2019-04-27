import os
import pytest

from testandconquer.env import Env
from testandconquer.env.codeship import Codeship


def test_create(codeship_basic_env):
    env = Env.create()
    assert env.name() is 'codeship'
    assert type(env) is Codeship


def test_settings_for_basic(codeship_basic_env):
    env = Env.create()
    assert env.build_id() == 'build_number'
    assert env.build_url() == 'build_url'
    assert env.context() == {
        'CI_PROJECT_ID': 'project_id',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_revision() == 'commit_id'
    assert env.vcs_revision_message() == 'message'


def test_settings_for_pro(codeship_pro_env):
    env = Env.create()
    assert env.build_id() == 'build_id'
    assert env.build_url() == 'build_url'
    assert env.context() == {
        'CI_PROJECT_ID': 'project_id',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_revision() == 'commit_id'
    assert env.vcs_revision_message() == 'message'


@pytest.fixture()
def codeship_basic_env():
    os.environ['CI'] = 'true'
    os.environ['CI_BRANCH'] = 'branch'
    os.environ['CI_BUILD_NUMBER'] = 'build_number'
    os.environ['CI_BUILD_URL'] = 'build_url'
    os.environ['CI_COMMIT_ID'] = 'commit_id'
    os.environ['CI_MESSAGE'] = 'message'
    os.environ['CI_NAME'] = 'codeship'
    os.environ['CI_PROJECT_ID'] = 'project_id'
    yield
    del os.environ['CI_BUILD_NUMBER']
    del os.environ['CI']
    del os.environ['CI_NAME']


@pytest.fixture()
def codeship_pro_env():
    os.environ['CI'] = 'true'
    os.environ['CI_BRANCH'] = 'branch'
    os.environ['CI_BUILD_ID'] = 'build_id'
    os.environ['CI_BUILD_URL'] = 'build_url'
    os.environ['CI_COMMIT_ID'] = 'commit_id'
    os.environ['CI_COMMIT_MESSAGE'] = 'message'
    os.environ['CI_NAME'] = 'codeship'
    os.environ['CI_PROJECT_ID'] = 'project_id'
    yield
    del os.environ['CI']
    del os.environ['CI_NAME']

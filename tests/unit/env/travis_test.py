import os
import pytest

from maketestsgofaster.env import Env
from maketestsgofaster.env.travis import Travis


def test_create(travis_env):
    env = Env.create()
    assert env.name() is 'travis'
    assert type(env) is Travis


def test_settings(travis_env):
    env = Env.create()
    assert env.build_id() == 'build_num'
    assert env.build_project() == 'org/repo'
    assert env.build_node() == 'job_num'
    assert env.context() == {
        'TRAVIS_EVENT_TYPE': 'event_type',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_pr() is None
    assert env.vcs_revision() == 'commit'
    assert env.vcs_revision_message() == 'commit_message'
    assert env.vcs_tag() == 'tag'


def test_settings_for_pr(travis_env_for_pr):
    env = Env.create()
    assert env.vcs_branch() == 'my_PR'
    assert env.vcs_pr() == 'pr'


@pytest.fixture()
def travis_env():
    os.environ['CI'] = 'true'
    os.environ['TRAVIS'] = 'true'
    os.environ['TRAVIS_BUILD_NUMBER'] = 'build_num'
    os.environ['TRAVIS_BRANCH'] = 'branch'
    os.environ['TRAVIS_COMMIT'] = 'commit'
    os.environ['TRAVIS_COMMIT_MESSAGE'] = 'commit_message'
    os.environ['TRAVIS_EVENT_TYPE'] = 'event_type'
    os.environ['TRAVIS_JOB_NUMBER'] = 'job_num'
    os.environ['TRAVIS_PULL_REQUEST'] = 'false'
    os.environ['TRAVIS_REPO_SLUG'] = 'org/repo'
    os.environ['TRAVIS_TAG'] = 'tag'
    yield
    del os.environ['CI']
    del os.environ['TRAVIS']


@pytest.fixture()
def travis_env_for_pr():
    os.environ['CI'] = 'true'
    os.environ['TRAVIS'] = 'true'
    os.environ['TRAVIS_PULL_REQUEST'] = 'pr'
    os.environ['TRAVIS_PULL_REQUEST_BRANCH'] = 'my_PR'
    yield
    del os.environ['CI']
    del os.environ['TRAVIS']

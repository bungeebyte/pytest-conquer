import os
import pytest

from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.env.drone import Drone


def test_create(drone_env):
    env = Env.create()
    assert env.name() is 'drone'
    assert type(env) is Drone


def test_settings(drone_env):
    env = Env.create()
    assert env.build_id() == 'build_num'
    assert env.build_url() == 'build_url'
    assert env.build_worker() == 'job_num'
    assert env.context() == {}
    assert env.vcs_branch() == 'branch'
    assert env.vcs_pr() is None
    assert env.vcs_repo() == 'repo_url'
    assert env.vcs_revision() == 'sha'
    assert env.vcs_tag() == 'tag'


def test_settings_for_pr(drone_env):
    os.environ['DRONE_PULL_REQUEST'] = 'pr_number'
    env = Env.create()
    assert env.vcs_pr() == 'pr_number'


@pytest.fixture()
def drone_env():
    os.environ['CI'] = 'true'
    os.environ['DRONE'] = 'true'
    os.environ['DRONE_BUILD_NUMBER'] = 'build_num'
    os.environ['DRONE_BUILD_LINK'] = 'build_url'
    os.environ['DRONE_COMMIT_BRANCH'] = 'branch'
    os.environ['DRONE_JOB_NUMBER'] = 'job_num'
    os.environ['DRONE_REPO_LINK'] = 'repo_url'
    os.environ['DRONE_COMMIT_SHA'] = 'sha'
    os.environ['DRONE_TAG'] = 'tag'
    yield
    del os.environ['CI']
    del os.environ['DRONE']

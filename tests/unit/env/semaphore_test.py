import os
import pytest

from maketestsgofaster.env import Env
from maketestsgofaster.env.semaphore import Semaphore


def test_create(semaphore_env):
    env = Env.create()
    assert env.name() is 'semaphore'
    assert type(env) is Semaphore


def test_settings(semaphore_env):
    env = Env.create()
    assert env.build_id() == 'build_num'
    assert env.build_job() == 'current_job'
    assert env.build_pool() == 'thread_count'
    assert env.build_node() == 'current_thread'
    assert env.context() == {
        'SEMAPHORE_JOB_COUNT': 'job_count',
        'SEMAPHORE_TRIGGER_SOURCE': 'trigger',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_pr() is None
    assert env.vcs_revision() == 'revision'


def test_settings_for_pr(semaphore_env):
    os.environ['PULL_REQUEST_NUMBER'] = '42'
    env = Env.create()
    assert env.vcs_pr() == '42'


@pytest.fixture()
def semaphore_env():
    os.environ['BRANCH_NAME'] = 'branch'
    os.environ['CI'] = 'true'
    os.environ['REVISION'] = 'revision'
    os.environ['SEMAPHORE'] = 'true'
    os.environ['SEMAPHORE_CURRENT_JOB'] = 'current_job'
    os.environ['SEMAPHORE_BUILD_NUMBER'] = 'build_num'
    os.environ['SEMAPHORE_CURRENT_THREAD'] = 'current_thread'
    os.environ['SEMAPHORE_JOB_COUNT'] = 'job_count'
    os.environ['SEMAPHORE_PROJECT_DIR'] = 'project_dir'
    os.environ['SEMAPHORE_REPO_SLUG'] = 'org/repo'
    os.environ['SEMAPHORE_THREAD_COUNT'] = 'thread_count'
    os.environ['SEMAPHORE_TRIGGER_SOURCE'] = 'trigger'
    yield
    del os.environ['CI']
    del os.environ['SEMAPHORE']

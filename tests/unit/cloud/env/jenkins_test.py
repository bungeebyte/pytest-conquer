import os
import pytest

from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.env.jenkins import Jenkins


def test_create(jenkins_env):
    env = Env.create()
    assert env.name() is 'jenkins'
    assert type(env) is Jenkins


def test_settings(jenkins_env):
    env = Env.create()
    assert env.build_id() == 'build_num'
    assert env.build_job() == 'job_name'
    assert env.build_url() == 'build_url'
    assert env.build_worker() == 'executor_num'
    assert env.context() == {
        'NODE_NAME': 'node_name',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_revision() == 'git_commit'


@pytest.fixture()
def jenkins_env():
    os.environ['BUILD_NUMBER'] = 'build_num'
    os.environ['BUILD_URL'] = 'build_url'
    os.environ['EXECUTOR_NUMBER'] = 'executor_num'
    os.environ['GIT_BRANCH'] = 'branch'
    os.environ['GIT_COMMIT'] = 'git_commit'
    os.environ['JENKINS_URL'] = 'jenkins_url'
    os.environ['JOB_NAME'] = 'job_name'
    os.environ['NODE_NAME'] = 'node_name'
    os.environ['WORKSPACE'] = 'workspace'
    yield
    del os.environ['JENKINS_URL']

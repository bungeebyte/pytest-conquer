import os
import pytest

from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.env.buildkite import Buildkite


def test_create(buildkite_env):
    env = Env.create()
    assert env.name() is 'buildkite'
    assert type(env) is Buildkite


def test_settings(buildkite_env):
    env = Env.create()
    assert env.build_id() == 'build_num'
    assert env.build_job() == 'specs'
    assert env.build_pool() == 'job_count'
    assert env.build_url() == 'build_url'
    assert env.build_worker() == 'job_num'
    assert env.context() == {
        'BUILDKITE_AGENT_NAME': 'agent_name',
        'BUILDKITE_COMMAND': 'command',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_repo() == 'repo_url'
    assert env.vcs_revision() == 'sha'
    assert env.vcs_revision_message() == 'commit_message'
    assert env.vcs_tag() == 'tag'


@pytest.fixture()
def buildkite_env():
    os.environ['BUILDKITE'] = 'true'
    os.environ['CI'] = 'true'
    os.environ['BUILDKITE_AGENT_NAME'] = 'agent_name'
    os.environ['BUILDKITE_BRANCH'] = 'branch'
    os.environ['BUILDKITE_BUILD_CHECKOUT_PATH'] = 'work_dir'
    os.environ['BUILDKITE_COMMIT'] = 'sha'
    os.environ['BUILDKITE_TAG'] = 'tag'
    os.environ['BUILDKITE_BUILD_NUMBER'] = 'build_num'
    os.environ['BUILDKITE_BUILD_URL'] = 'build_url'
    os.environ['BUILDKITE_COMMAND'] = 'command'
    os.environ['BUILDKITE_MESSAGE'] = 'commit_message'
    os.environ['BUILDKITE_LABEL'] = 'specs'
    os.environ['BUILDKITE_ORGANIZATION_SLUG'] = 'org'
    os.environ['BUILDKITE_PARALLEL_JOB'] = 'job_num'
    os.environ['BUILDKITE_PARALLEL_JOB_COUNT'] = 'job_count'
    os.environ['BUILDKITE_PIPELINE_SLUG'] = 'repo'
    os.environ['BUILDKITE_REPO'] = 'repo_url'
    yield
    del os.environ['BUILDKITE']
    del os.environ['CI']

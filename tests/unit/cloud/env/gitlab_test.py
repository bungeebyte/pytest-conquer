import os
import pytest

from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.env.gitlab import GitLab


def test_create(gitlab9_env):
    env = Env.create()
    assert env.name() is 'gitlab'
    assert type(env) is GitLab


def test_settings_version_9(gitlab9_env):
    env = Env.create()
    assert env.build_id() == 'job_name'
    assert env.build_job() == 'job_stage'
    assert env.build_worker() == 'runner_id'
    assert env.context() == {
        'CI_RUNNER_REVISION': 'runner_revision',
        'CI_RUNNER_VERSION': 'runner_version',
        'CI_SERVER_REVISION': 'server_revision',
        'CI_SERVER_VERSION': 'server_version',
    }
    assert env.vcs_branch() == 'ref_name'
    assert env.vcs_repo() == 'repo_url'
    assert env.vcs_revision() == 'sha'
    assert env.vcs_tag() == 'tag'


def test_settings_version_8(gitlab8_env):
    env = Env.create()
    assert env.build_id() == 'job_name'
    assert env.build_job() == 'job_stage'
    assert env.build_worker() == 'runner_id'
    assert env.context() == {
        'CI_RUNNER_REVISION': 'runner_revision',
        'CI_RUNNER_VERSION': 'runner_version',
        'CI_SERVER_REVISION': 'server_revision',
        'CI_SERVER_VERSION': 'server_version',
    }
    assert env.vcs_branch() == 'ref_name'
    assert env.vcs_revision() == 'sha'
    assert env.vcs_tag() == 'tag'


@pytest.fixture()
def gitlab9_env():
    os.environ['CI'] = 'true'
    os.environ['CI_COMMIT_REF_NAME'] = 'ref_name'
    os.environ['CI_COMMIT_SHA'] = 'sha'
    os.environ['CI_COMMIT_TAG'] = 'tag'
    os.environ['CI_JOB_ID'] = 'job_id'
    os.environ['CI_JOB_NAME'] = 'job_name'
    os.environ['CI_JOB_STAGE'] = 'job_stage'
    os.environ['CI_PROJECT_DIR'] = 'project_dir'
    os.environ['CI_PROJECT_NAME'] = 'project_name'
    os.environ['CI_PROJECT_NAMESPACE'] = 'org'
    os.environ['CI_REPOSITORY_URL'] = 'repo_url'
    os.environ['CI_RUNNER_ID'] = 'runner_id'
    os.environ['CI_RUNNER_REVISION'] = 'runner_revision'
    os.environ['CI_RUNNER_VERSION'] = 'runner_version'
    os.environ['CI_SERVER_REVISION'] = 'server_revision'
    os.environ['CI_SERVER_VERSION'] = 'server_version'
    os.environ['GITLAB_CI'] = 'true'
    yield
    del os.environ['CI']
    del os.environ['GITLAB_CI']


@pytest.fixture()
def gitlab8_env():
    os.environ['CI'] = 'true'
    os.environ['CI_BUILD_REF_NAME'] = 'ref_name'
    os.environ['CI_BUILD_REF'] = 'sha'
    os.environ['CI_BUILD_TAG'] = 'tag'
    os.environ['CI_BUILD_ID'] = 'job_id'
    os.environ['CI_JOB_NAME'] = 'job_name'
    os.environ['CI_JOB_STAGE'] = 'job_stage'
    os.environ['CI_PROJECT_URL'] = 'build_url'
    os.environ['CI_PROJECT_DIR'] = 'project_dir'
    os.environ['CI_PROJECT_NAME'] = 'project_name'
    os.environ['CI_PROJECT_NAMESPACE'] = 'org'
    os.environ['CI_REPOSITORY_URL'] = 'repo_url'
    os.environ['CI_RUNNER_ID'] = 'runner_id'
    os.environ['CI_RUNNER_REVISION'] = 'runner_revision'
    os.environ['CI_RUNNER_VERSION'] = 'runner_version'
    os.environ['CI_SERVER_REVISION'] = 'server_revision'
    os.environ['CI_SERVER_VERSION'] = 'server_version'
    os.environ['GITLAB_CI'] = 'true'
    yield
    del os.environ['CI']
    del os.environ['GITLAB_CI']

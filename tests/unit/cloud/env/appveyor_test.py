import os
import pytest

from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.env.appveyor import AppVeyor


def test_create(appveyor_env):
    env = Env.create()
    assert env.name() is 'appveyor'
    assert type(env) is AppVeyor


def test_settings(appveyor_env):
    env = Env.create()
    assert env.build_id() == 'build_id'
    assert env.build_job() == 'job'
    assert env.build_project() == 'org/repo'
    assert env.build_worker() == 'job_num'
    assert env.context() == {
        'APPVEYOR_RE_BUILD': 'True',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_pr() is None
    assert env.vcs_revision() == 'sha'
    assert env.vcs_revision_message() == 'commit_message'
    assert env.vcs_tag() == 'tag'


def test_settings_for_pr(appveyor_env):
    os.environ['APPVEYOR_PULL_REQUEST_NUMBER'] = 'pr_number'
    env = Env.create()
    assert env.vcs_pr() == 'pr_number'


@pytest.fixture()
def appveyor_env():
    os.environ['APPVEYOR'] = 'true'
    os.environ['APPVEYOR_BUILD_ID'] = 'build_id'
    os.environ['APPVEYOR_JOB_NAME'] = 'job'
    os.environ['APPVEYOR_JOB_NUMBER'] = 'job_num'
    os.environ['APPVEYOR_PROJECT_SLUG'] = 'org/repo'
    os.environ['APPVEYOR_RE_BUILD'] = 'True'
    os.environ['APPVEYOR_REPO_BRANCH'] = 'branch'
    os.environ['APPVEYOR_REPO_COMMIT'] = 'sha'
    os.environ['APPVEYOR_REPO_COMMIT_MESSAGE'] = 'commit_message'
    os.environ['APPVEYOR_REPO_NAME'] = 'org/repo'
    os.environ['APPVEYOR_REPO_TAG_NAME'] = 'tag'
    os.environ['CI'] = 'true'
    yield
    del os.environ['CI']
    del os.environ['APPVEYOR']

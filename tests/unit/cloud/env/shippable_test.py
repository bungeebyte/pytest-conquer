import os
import pytest

from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.env.shippable import Shippable


def test_create(shippable_env):
    env = Env.create()
    assert env.name() is 'shippable'
    assert type(env) is Shippable


def test_settings(shippable_env):
    env = Env.create()
    assert env.build_id() == 'build_num'
    assert env.build_url() == 'build_url'
    assert env.build_worker() == 'job_id'
    assert env.context() == {
        'PROJECT_ID': 'project_id',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_pr() is None
    assert env.vcs_repo() == 'repo_url'
    assert env.vcs_revision() == 'sha'
    assert env.vcs_revision_message() == 'commit_message'
    assert env.vcs_tag() == 'tag'


def test_settings_for_pr(shippable_env):
    os.environ['IS_PULL_REQUEST'] = 'true'
    os.environ['PULL_REQUEST'] = 'pr_number'
    env = Env.create()
    assert env.vcs_pr() == 'pr_number'


@pytest.fixture()
def shippable_env():
    os.environ['CI'] = 'true'
    os.environ['BRANCH'] = 'branch'
    os.environ['BUILD_NUMBER'] = 'build_num'
    os.environ['BUILD_URL'] = 'build_url'
    os.environ['COMMIT'] = 'sha'
    os.environ['COMMIT_MESSAGE'] = 'commit_message'
    os.environ['GIT_TAG_NAME'] = 'tag'
    os.environ['IS_GIT_TAG'] = 'true'
    os.environ['JOB_NUMBER'] = 'job_id'
    os.environ['ORG_NAME'] = 'org'
    os.environ['PROJECT_ID'] = 'project_id'
    os.environ['REPO_NAME'] = 'repo'
    os.environ['REPOSITORY_URL'] = 'repo_url'
    os.environ['SHIPPABLE'] = 'true'
    os.environ['TRAVIS'] = 'true'  # no mistake
    yield
    del os.environ['CI']
    del os.environ['SHIPPABLE']
    del os.environ['TRAVIS']

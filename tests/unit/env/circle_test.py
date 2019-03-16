import os
import pytest

from maketestsgofaster.env import Env
from maketestsgofaster.env.circle import Circle


def test_create(circle_env):
    env = Env.create()
    assert env.name() is 'circle'
    assert type(env) is Circle


def test_settings(circle_env):
    env = Env.create()
    assert env.build_id() == 'build_num'
    assert env.build_job() == 'job'
    assert env.build_pool() == 'node_total'
    assert env.build_url() == 'build_url'
    assert env.build_node() == 'node_index'
    assert env.context() == {
        'CIRCLE_STAGE': 'stage',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_pr() is None
    assert env.vcs_repo() == 'repo_url'
    assert env.vcs_revision() == 'sha'
    assert env.vcs_tag() == 'tag'


def test_settings_for_pr(circle_env):
    os.environ['CIRCLE_PR_NUMBER'] = 'pr_number'
    env = Env.create()
    assert env.vcs_pr() == 'pr_number'


@pytest.fixture()
def circle_env():
    os.environ['CI'] = 'true'
    os.environ['CIRCLECI'] = 'true'
    os.environ['CIRCLE_BUILD_NUM'] = 'build_num'
    os.environ['CIRCLE_BUILD_URL'] = 'build_url'
    os.environ['CIRCLE_BRANCH'] = 'branch'
    os.environ['CIRCLE_JOB'] = 'job'
    os.environ['CIRCLE_NODE_TOTAL'] = 'node_total'
    os.environ['CIRCLE_NODE_INDEX'] = 'node_index'
    os.environ['CIRCLE_PROJECT_USERNAME'] = 'org'
    os.environ['CIRCLE_PROJECT_REPONAME'] = 'repo'
    os.environ['CIRCLE_REPOSITORY_URL'] = 'repo_url'
    os.environ['CIRCLE_SHA1'] = 'sha'
    os.environ['CIRCLE_STAGE'] = 'stage'
    os.environ['CIRCLE_TAG'] = 'tag'
    yield
    del os.environ['CI']
    del os.environ['CIRCLECI']

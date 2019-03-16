import os
import pytest

from maketestsgofaster.env import Env
from maketestsgofaster.env.bamboo import Bamboo


def test_create(bamboo_env):
    env = Env.create()
    assert env.name() is 'bamboo'
    assert type(env) is Bamboo


def test_settings(bamboo_env):
    env = Env.create()
    assert env.build_id() == 'build_num'
    assert env.build_project() == 'build_project'
    assert env.build_url() == 'build_url'
    assert env.build_node() == 'job_num'
    assert env.context() == {
        'bamboo.buildKey': 'BAM-MAIN-JOBX',
    }
    assert env.vcs_branch() == 'branch'
    assert env.vcs_repo() == 'repo_url'
    assert env.vcs_revision() == 'sha'
    assert env.vcs_type() == 'hg'


@pytest.fixture()
def bamboo_env():
    os.environ['CI'] = 'true'
    os.environ['bamboo.buildKey'] = 'BAM-MAIN-JOBX'
    os.environ['bamboo.buildNumber'] = 'build_num'
    os.environ['bamboo.planKey'] = 'build_project'
    os.environ['bamboo.planRepository.branch'] = 'branch'
    os.environ['bamboo.planRepository.repositoryUrl'] = 'repo_url'
    os.environ['bamboo.planRepository.revision'] = 'sha'
    os.environ['bamboo.planRepository.type'] = 'hg'
    os.environ['bamboo.resultsUrl'] = 'build_url'
    os.environ['bamboo.shortJobKey'] = 'job_num'
    yield
    del os.environ['CI']
    del os.environ['bamboo.buildKey']

import os
import pytest

from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.env.teamcity import TeamCity


def test_create(teamcity_version):
    env = Env.create()
    assert env.name() is 'teamcity'
    assert type(env) is TeamCity


def test_settings(teamcity_version):
    env = Env.create()
    assert env.build_id() == 'build_num'
    assert env.build_project() == 'build_project'
    assert env.context() == {
        'TEAMCITY_VERSION': 'tc_version',
    }
    assert env.vcs_revision() == 'sha'


@pytest.fixture()
def teamcity_version():
    os.environ['CI'] = 'true'
    os.environ['BUILD_NUMBER'] = 'build_num'
    os.environ['BUILD_VCS_NUMBER'] = 'sha'
    os.environ['TEAMCITY_PROJECT_NAME'] = 'build_project'
    os.environ['TEAMCITY_VERSION'] = 'tc_version'
    yield
    del os.environ['CI']
    del os.environ['TEAMCITY_VERSION']

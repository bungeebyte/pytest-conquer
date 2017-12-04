import os
import pytest

from maketestsgofaster.cloud.env import Env


def test_get_default():
    env = Env.create()
    assert env.get('build_dir') == os.getcwd()
    assert env.get('none_existing') is None


def test_get_from_env(custom_env):
    env = Env.create()
    assert env.get('build_dir') == 'env'


def test_get_from_override(custom_env):
    env = Env.create({'build_dir': 'override'})
    assert env.get('build_dir') == 'override'


@pytest.fixture()
def custom_env():
    os.environ['MTGF_BUILD_DIR'] = 'env'
    yield
    del os.environ['MTGF_BUILD_DIR']

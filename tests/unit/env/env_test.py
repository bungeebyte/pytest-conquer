import os
import pytest

from testandconquer.env import Env


def test_get_default():
    env = Env.create()
    assert env.get('build_dir') == os.getcwd()
    assert env.get('none_existing') is None


def test_get_from_env(custom_env):
    env = Env.create()
    assert env.get('build_id') == '42'
    assert env.get('build_node') == '42'


def test_get_from_override(custom_env):
    env = Env.create({'build_dir': 'override'})
    assert env.get('build_dir') == 'override'


@pytest.fixture()
def custom_env():
    os.environ['conquer_build_node'] = '42'
    os.environ['CONQUER_BUILD_ID'] = '42'
    yield
    del os.environ['CONQUER_BUILD_ID']
    del os.environ['conquer_build_node']

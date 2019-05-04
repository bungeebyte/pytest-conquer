import os

from unittest import mock

from testandconquer.env import Env


class TestEnv():

    def test_get_variable_from_args(self):
        env = Env({
            'system_provider': 'args-provider',
        })
        assert env.get('system_provider') == 'args-provider'

    def test_get_variable_from_env(self):
        os.environ['CONQUER_SYSTEM_PROVIDER'] = 'env-provider'
        env = Env({})
        assert env.get('system_provider') == 'env-provider'
        del os.environ['CONQUER_SYSTEM_PROVIDER']

    def test_get_variable_from_file(self):
        env = Env({})
        env.init_file('pytest.ini')
        assert env.get('system_provider') == 'config-provider'

    def test_get_variable_from_mapping(self):
        os.environ['CI_NAME'] = 'mapping-provider'
        os.environ['CI_NODE'] = 'node'
        env = Env({})
        client_mock = mock.Mock()
        client_mock.get = lambda _url: [{'name': 'mapping-provider', 'conditions': ['CI_NAME'], 'mapping': {'build_node': 'CI_NODE'}}]
        env.init_mapping(client_mock)
        assert env.get('system_provider') == 'mapping-provider'
        assert env.get('build_node') == 'node'
        del os.environ['CI_NAME']
        del os.environ['CI_NODE']

    def test_get_variable_from_defaults(self):
        env = Env({})
        assert env.get('system_provider') == 'custom'

    def test_get_nonexistent_variable(self):
        env = Env({})
        assert env.get('nonexistent') is None

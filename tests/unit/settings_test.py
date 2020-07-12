import os

import pytest

from testandconquer.settings import Settings


class TestSettings():

    def test_api_key(self):
        settings = Settings({'api_key': 'MY API KEY'})
        assert settings.api_key == 'MY API KEY'

    def test_api_key_missing(self):
        with pytest.raises(ValueError, match="missing API key, please set 'api_key'"):
            Settings({}).api_key

    def test_api_retry_limit_default(self):
        settings = Settings({})
        assert settings.api_retry_limit == 6

    def test_api_retry_limit(self):
        settings = Settings({'api_retry_limit': '1'})
        assert settings.api_retry_limit == 1

    def test_api_wait_limit_default(self):
        settings = Settings({})
        assert settings.api_wait_limit == 60

    def test_api_wait_limit(self):
        settings = Settings({'api_wait_limit': '1'})
        assert settings.api_wait_limit == 1

    def test_api_domains(self):
        settings = Settings({})
        assert settings.api_domain == 'testandconquer.com'
        assert settings.api_domain_fallback == 'testconquer.com'

        settings = Settings({'api_domain': '0.0.0.0'})
        assert settings.api_domain == '0.0.0.0'

    def test_build_id(self):
        settings = Settings({'build_id': 'ABCD'})
        assert settings.build_id == 'ABCD'

    def test_build_id_missing(self):
        with pytest.raises(ValueError, match="missing build ID, please set 'build_id'"):
            Settings({}).build_id

    def test_build_job(self):
        settings = Settings({'build_job': 'JOB#1'})
        assert settings.build_job == 'JOB#1'

    def test_build_pool(self):
        settings = Settings({'build_pool': 2})
        assert settings.build_pool == 2

    def test_build_pool_default(self):
        settings = Settings({})
        assert settings.build_pool == 0

    def test_build_dir(self):
        settings = Settings({'build_dir': '/app'})
        assert settings.build_dir == '/app'

    def test_build_node(self):
        settings = Settings({'build_node': '<node>'})
        assert settings.build_node == '<node>'

    def test_build_dir_default(self, mocker):
        cwd = mocker.patch('os.getcwd')
        cwd.return_value = '/app'

        settings = Settings({})
        assert settings.build_dir == '/app'

    def test_client_name(self):
        settings = Settings({})
        assert settings.client_name == 'pytest-conquer'

    def test_client_version(self):
        settings = Settings({})
        assert settings.client_version == '1.0'

    def test_debug(self):
        settings = Settings({'debug': True})
        assert settings.debug is True
        settings = Settings({'debug': 'true'})
        assert settings.debug is True
        settings = Settings({'debug': 'TRUE'})
        assert settings.debug is True

    def test_debug_default(self):
        settings = Settings({})
        assert settings.debug is False

    def test_enabled(self):
        settings = Settings({'enabled': True})
        assert settings.enabled is True
        settings = Settings({'enabled': 'true'})
        assert settings.enabled is True
        settings = Settings({'enabled': 'TRUE'})
        assert settings.enabled is True

    def test_enabled_default(self):
        settings = Settings({'enabled': False})
        assert settings.enabled is False

    def test_platform_name(self):
        settings = Settings({})
        assert settings.platform_name == 'python'

    def test_platform_version(self, mocker):
        py_version = mocker.patch('platform.python_version')
        py_version.return_value = '_VERSION_'

        settings = Settings({})
        assert settings.platform_version == '_VERSION_'

    def test_system_context(self):
        settings = Settings({'system_context': {'env': 'var'}})
        assert settings.system_context == {'env': 'var'}

    def test_system_provider(self):
        settings = Settings({'system_provider': 'my-system'})
        assert settings.system_provider == 'my-system'

    def test_vcs_branch(self):
        settings = Settings({'vcs_branch': 'master'})
        assert settings.vcs_branch == 'master'

    def test_vcs_repo(self):
        settings = Settings({'vcs_repo': 'https://github.com'})
        assert settings.vcs_repo == 'https://github.com'

    def test_vcs_revision(self):
        settings = Settings({'vcs_revision': '347adksanv'})
        assert settings.vcs_revision == '347adksanv'

    def test_vcs_revision_message(self):
        settings = Settings({'vcs_revision_message': 'commit'})
        assert settings.vcs_revision_message == 'commit'

    def test_vcs_tag(self):
        settings = Settings({'vcs_tag': '1.0'})
        assert settings.vcs_tag == '1.0'

    def test_get_nonexistent_variable(self):
        settings = Settings({})
        assert settings.nonexistent is None


class TestSettingsInit():

    def test_get_variable_from_args(self):
        settings = Settings({'system_provider': 'args-provider'})
        assert settings.system_provider == 'args-provider'

    def test_get_variable_from_env(self):
        os.environ['CONQUER_SYSTEM_PROVIDER'] = 'env-provider'
        settings = Settings({})
        assert settings.system_provider == 'env-provider'
        del os.environ['CONQUER_SYSTEM_PROVIDER']

    def test_validate_variables_from_env(self, invalid_env):
        with pytest.raises(ValueError, match="unsupported key 'CONQUER_NON_EXISTING_VAR' in environment variables"):
            Settings({})

    def test_get_variable_from_file(self):
        settings = Settings({})
        settings.init_from_file('pytest.ini')
        assert settings.system_provider == 'config-provider'

    # @pytest.mark.asyncio()
    # async def test_get_variable_from_mapping(self):
    #     os.environ['CI_name'] = 'mapping-provider'
    #     os.environ['ENV_node'] = 'NODE'
    #     os.environ['env_HOST'] = 'HOST'
    #     settings = Settings({})

    #     # when provider matches
    #     envs = [{'name': 'mapping-provider', 'conditions': ['ci_NAME'], 'mapping': {'build_NODE': 'ENV_NODE', 'system_context': ['ENV_HOST']}}]
    #     assert settings.on_server_message(MessageType.Envs.value, envs) == (MessageType.Envs, 'mapping-provider')
    #     assert settings.system_provider == 'mapping-provider'
    #     assert settings.build_node == 'NODE'
    #     assert settings.system_context == {'ENV_HOST': 'HOST'}

    #     # when provider doesn't match
    #     envs = []
    #     assert settings.on_server_message(MessageType.Envs.value, envs) == (MessageType.Envs, 'unknown')
    #     assert settings.system_provider == 'unknown'
    #     assert settings.build_node != 'NODE'

    #     del os.environ['CI_name']
    #     del os.environ['ENV_node']
    #     del os.environ['env_HOST']

    def test_get_variable_from_defaults(self):
        settings = Settings({})
        assert settings.system_provider is None

    def test_validate_config_file_entries(self):
        with pytest.raises(ValueError, match="unsupported key 'wrong_var' in config file tests/pytest.invalid.ini"):
            settings = Settings({})
            settings.init_from_file('tests/pytest.invalid.ini')

    @pytest.fixture
    def invalid_env(self):
        os.environ['CONQUER_NON_EXISTING_VAR'] = 'nonsense'
        yield
        del os.environ['CONQUER_NON_EXISTING_VAR']

import sys

import pytest

from maketestsgofaster.cloud.settings import Settings


class TestInitSettings():

    def test_api_key(self):
        settings = Settings(MockedEnv({
            'api_key': 'MY API KEY',
        }))
        assert settings.api_key == 'MY API KEY'

    def test_api_retries_default(self):
        settings = Settings(MockedEnv())
        assert settings.api_retries == 6

    def test_api_retries(self):
        settings = Settings(MockedEnv({
            'api_retries': '1',
        }))
        assert settings.api_retries == 1

    def test_api_timeout_default(self):
        settings = Settings(MockedEnv())
        assert settings.api_timeout == 10

    def test_api_timeout(self):
        settings = Settings(MockedEnv({
            'api_timeout': '1',
        }))
        assert settings.api_timeout == 1

    def test_api_retry_cap_default(self):
        settings = Settings(MockedEnv())
        assert settings.api_retry_cap == 60

    def test_api_retry_cap(self):
        settings = Settings(MockedEnv({
            'api_retry_cap': '1',
        }))
        assert settings.api_retry_cap == 1

    def test_api_url(self):
        settings = Settings(MockedEnv({
            'api_url': 'http://0.0.0.0',
        }))
        assert settings.api_urls == ['http://0.0.0.0']

    def test_api_url_default(self):
        settings = Settings(MockedEnv())
        assert settings.api_urls == ['https://scheduler.maketestsgofaster.com', 'https://scheduler.maketestsgofaster.co']

    def test_build_id(self):
        settings = Settings(MockedEnv({
            'build_id': 'ABCD',
        }))
        assert settings.build_id == 'ABCD'

    def test_build_job(self):
        settings = Settings(MockedEnv({
            'build_job': 'JOB#1',
        }))
        assert settings.build_job == 'JOB#1'

    def test_build_pool(self):
        settings = Settings(MockedEnv({
            'build_pool': 2,
        }))
        assert settings.build_pool == 2

    def test_build_pool_default(self):
        settings = Settings(MockedEnv())
        assert settings.build_pool == 0

    def test_build_dir(self):
        settings = Settings(MockedEnv({
            'build_dir': '/app',
        }))
        assert settings.build_dir == '/app'

    def test_build_node(self):
        settings = Settings(MockedEnv({
            'build_node': '<node>',
        }))
        assert settings.build_node == '<node>'

    def test_build_dir_default(self, mocker):
        py_version = mocker.patch('os.getcwd')
        py_version.return_value = '/app'

        settings = Settings(MockedEnv())
        assert settings.build_dir == '/app'

    def test_client_name(self):
        settings = Settings(MockedEnv())
        assert settings.client_name == 'python-official'

    def test_client_version(self):
        settings = Settings(MockedEnv())
        assert settings.client_version == '1.0'

    def test_platform_name(self):
        settings = Settings(MockedEnv())
        assert settings.platform_name == 'python'

    def test_platform_version(self, mocker):
        py_version = mocker.patch('platform.python_version')
        py_version.return_value = '_VERSION_'

        settings = Settings(MockedEnv())
        assert settings.platform_version == '_VERSION_'

    def test_system_name(self):
        settings = Settings(MockedEnv({
            'name': 'my-context',
        }))
        assert settings.system_name

    def test_system_context(self):
        settings = Settings(MockedEnv({
            'context': {
                'env': 'var',
            },
        }))
        assert settings.system_context == {
            'env': 'var',
        }

    def test_vcs_branch(self):
        settings = Settings(MockedEnv({
            'vcs_branch': 'master',
        }))
        assert settings.vcs_branch == 'master'

    def test_vcs_repo(self):
        settings = Settings(MockedEnv({
            'vcs_repo': 'https://github.com',
        }))
        assert settings.vcs_repo == 'https://github.com'

    def test_vcs_revision(self):
        settings = Settings(MockedEnv({
            'vcs_revision': '347adksanv',
        }))
        assert settings.vcs_revision == '347adksanv'

    def test_vcs_revision_message(self):
        settings = Settings(MockedEnv({
            'vcs_revision_message': 'commit',
        }))
        assert settings.vcs_revision_message == 'commit'

    def test_vcs_tag(self):
        settings = Settings(MockedEnv({
            'vcs_tag': '1.0',
        }))
        assert settings.vcs_tag == '1.0'

    def test_fails_for_python2(self):
        with pytest.raises(SystemExit):
            env = MockedEnv()
            env.python_version = lambda: (2, 7)
            Settings(env)


class TestValidateSettings():

    valid_settings = {
        'api_key': 'MY API KEY',
        'build_id': '12',
        'vcs_branch': 'master',
        'vcs_revision': '0572ida1',
    }

    invalid_scenarios = [
        (lambda data: data.pop('api_key'), "missing API key, please set 'api_key'"),
        (lambda data: data.pop('build_id'), "missing build ID, please set 'build_id'"),
        (lambda data: data.pop('vcs_branch'), "missing repository branch, please set 'vcs_branch'"),
        (lambda data: data.pop('vcs_revision'), "missing repository revision, please set 'vcs_revision'"),
    ]

    def test_valid_settings(self):
        Settings(MockedEnv(self.valid_settings)).validate()

    @pytest.mark.parametrize('fn,expected', invalid_scenarios)
    def test_validation(self, fn, expected):
        with pytest.raises(RuntimeError, match=expected):
            data = self.valid_settings.copy()
            fn(data)
            Settings(MockedEnv(data)).validate()


class MockedEnv():
    def __init__(self, data={}):
        self.data = data

    def context(self):
        return self.data.get('context')

    def get(self, name):
        return self.data.get(name)

    def python_version(self):
        return sys.version_info

    def name(self):
        return self.data.get('name')

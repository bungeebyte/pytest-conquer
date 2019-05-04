import pytest

from testandconquer.settings import Settings

from tests.IT.mock.env import MockEnv


class TestSettings():

    def test_api_key(self):
        settings = Settings(MockEnv({
            'api_key': 'MY API KEY',
        }))
        assert settings.api_key == 'MY API KEY'

    def test_api_retries_default(self):
        settings = Settings(MockEnv())
        assert settings.api_retries == 6

    def test_api_retries(self):
        settings = Settings(MockEnv({
            'api_retries': '1',
        }))
        assert settings.api_retries == 1

    def test_api_timeout_default(self):
        settings = Settings(MockEnv())
        assert settings.api_timeout == 10

    def test_api_timeout(self):
        settings = Settings(MockEnv({
            'api_timeout': '1',
        }))
        assert settings.api_timeout == 1

    def test_api_retry_cap_default(self):
        settings = Settings(MockEnv())
        assert settings.api_retry_cap == 60

    def test_api_retry_cap(self):
        settings = Settings(MockEnv({
            'api_retry_cap': '1',
        }))
        assert settings.api_retry_cap == 1

    def test_api_url(self):
        settings = Settings(MockEnv({
            'api_url': 'http://0.0.0.0',
        }))
        assert settings.api_urls == ['http://0.0.0.0']

    def test_api_url_default(self):
        settings = Settings(MockEnv())
        assert settings.api_urls == ['https://scheduler.testandconquer.com', 'https://scheduler.testconquer.com']

    def test_build_id(self):
        settings = Settings(MockEnv({
            'build_id': 'ABCD',
        }))
        assert settings.build_id == 'ABCD'

    def test_build_job(self):
        settings = Settings(MockEnv({
            'build_job': 'JOB#1',
        }))
        assert settings.build_job == 'JOB#1'

    def test_build_pool(self):
        settings = Settings(MockEnv({
            'build_pool': 2,
        }))
        assert settings.build_pool == 2

    def test_build_pool_default(self):
        settings = Settings(MockEnv())
        assert settings.build_pool == 0

    def test_build_dir(self):
        settings = Settings(MockEnv({
            'build_dir': '/app',
        }))
        assert settings.build_dir == '/app'

    def test_build_node(self):
        settings = Settings(MockEnv({
            'build_node': '<node>',
        }))
        assert settings.build_node == '<node>'

    def test_build_dir_default(self, mocker):
        cwd = mocker.patch('os.getcwd')
        cwd.return_value = '/app'

        settings = Settings(MockEnv())
        assert settings.build_dir == '/app'

    def test_client_name(self):
        settings = Settings(MockEnv())
        assert settings.client_name == 'python-official'

    def test_client_version(self):
        settings = Settings(MockEnv())
        assert settings.client_version == '1.0'

    def test_platform_name(self):
        settings = Settings(MockEnv())
        assert settings.platform_name == 'python'

    def test_platform_version(self, mocker):
        py_version = mocker.patch('platform.python_version')
        py_version.return_value = '_VERSION_'

        settings = Settings(MockEnv())
        assert settings.platform_version == '_VERSION_'

    def test_client_workers(self, mocker):
        cpu_count = mocker.patch('multiprocessing.cpu_count')
        cpu_count.return_value = 8

        settings = Settings(MockEnv({
            'workers': 'max',
        }))
        assert settings.client_workers == 8

    def test_client_workers_default(self, mocker):
        settings = Settings(MockEnv())
        assert settings.client_workers == 1

    def test_system_context(self):
        settings = Settings(MockEnv({
            'system_context': {
                'env': 'var',
            },
        }))
        assert settings.system_context == {
            'env': 'var',
        }

    def test_system_provider(self):
        settings = Settings(MockEnv({
            'system_provider': 'my-system',
        }))
        assert settings.system_provider == 'my-system'

    def test_vcs_branch(self):
        settings = Settings(MockEnv({
            'vcs_branch': 'master',
        }))
        assert settings.vcs_branch == 'master'

    def test_vcs_repo(self):
        settings = Settings(MockEnv({
            'vcs_repo': 'https://github.com',
        }))
        assert settings.vcs_repo == 'https://github.com'

    def test_vcs_revision(self):
        settings = Settings(MockEnv({
            'vcs_revision': '347adksanv',
        }))
        assert settings.vcs_revision == '347adksanv'

    def test_vcs_revision_message(self):
        settings = Settings(MockEnv({
            'vcs_revision_message': 'commit',
        }))
        assert settings.vcs_revision_message == 'commit'

    def test_vcs_tag(self):
        settings = Settings(MockEnv({
            'vcs_tag': '1.0',
        }))
        assert settings.vcs_tag == '1.0'

    def test_fails_for_python2(self):
        with pytest.raises(SystemExit):
            env = MockEnv()
            env.python_version = lambda: (2, 7)
            Settings(env)


class TestSettingsValidation():

    valid_settings = {
        'api_key': 'MY API KEY',
        'build_id': '12',
        'vcs_branch': 'master',
        'vcs_revision': '0572ida1',
    }

    def test_valid_settings(self):
        Settings(MockEnv(self.valid_settings)).validate()

    @pytest.mark.wip
    @pytest.mark.parametrize('fn,expected', [
        (lambda data: data.pop('api_key'), "missing API key, please set 'api_key'"),
        (lambda data: data.pop('build_id'), "missing build ID, please set 'build_id'"),
        (lambda data: data.pop('vcs_branch'), "missing repository branch, please set 'vcs_branch'"),
        (lambda data: data.pop('vcs_revision'), "missing repository revision, please set 'vcs_revision'"),
    ])
    def test_validation(self, fn, expected):
        with pytest.raises(ValueError, match=expected):
            data = self.valid_settings.copy()
            fn(data)
            Settings(MockEnv(data)).validate()

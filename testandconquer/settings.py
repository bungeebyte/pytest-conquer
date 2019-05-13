import configparser
import multiprocessing
import os
import platform
import uuid
import sys

import psutil
from enum import Enum

from testandconquer import __version__, debug_logger
from testandconquer.client import Client
from testandconquer.git import Git


CONFIG_SECTION = 'conquer'
ENV_PREFIX = 'CONQUER_'


class Capability(Enum):
    Fixtures = 'fixtures'
    IsolatedProcess = 'isolated_process'
    LifecycleTimings = 'lifecycle_timings'
    SplitByFile = 'split_by_file'


class Settings():
    def __init__(self, args):
        self.args = args
        self.config = None
        self.mapping = None
        self.upcased_environ = dict()
        for key in os.environ:
            self.upcased_environ[key.upper()] = os.environ[key]
        self.static_settings = StaticSettings()
        self.default_settings = DefaultSettings()

    def init_env(self, client=None):
        self.__pre_init_validate()
        self.__init_mapping(client or Client(self))  # we need to get the env variable mappings from the server first
        self.__post_init_validate()

    def init_file(self, path):
        self.config = configparser.ConfigParser()
        self.config.read(path)

        if self.debug is True:
            debug_logger()

    def __init_mapping(self, client):
        envs = client.get('/envs')
        for env in envs:
            is_match = True
            for condition in env['conditions']:
                if condition not in self.upcased_environ:
                    is_match = False
                    break
            if is_match:
                self.mapping = env['mapping']
                self.args['system_provider'] = env['name']
                break

    def __pre_init_validate(self):
        if self.api_key is None:
            raise ValueError("missing API key, please set 'api_key'")

    def __post_init_validate(self):
        if self.build_id is None:
            raise ValueError("missing build ID, please set 'build_id'")
        if self.vcs_branch is None:
            raise ValueError("missing repository branch, please set 'vcs_branch'")
        if self.vcs_revision is None:
            raise ValueError("missing repository revision, please set 'vcs_revision'")

    @property
    def client_enabled(self):
        val = self.__getattr__('enabled') or False
        if val is True or val is False:
            return val
        return val.lower() == 'true'

    @property
    def client_workers(self):
        val = self.__getattr__('workers') or '1'
        if val == 'max':
            return multiprocessing.cpu_count()
        elif not val.isdigit():
            raise ValueError("'workers' must be an integer")
        else:
            return int(val)

    def __getattr__(self, name):
        default_val = None
        default_method = getattr(self.default_settings, name, None)
        if default_method:
            default_val = default_method()

        # 1) static values (can't be overriden)
        method = getattr(self.static_settings, name, None)
        if method:
            return method()

        # 2) plugin arguments
        if name in self.args:
            val = self.args.get(name)
            if val is not None:
                return self.__convert(val, default_val)

        # 3) environment variables
        env_name = (ENV_PREFIX + name).upper()
        if env_name in self.upcased_environ:
            return self.__convert(self.upcased_environ[env_name], default_val)

        # 4) local config file
        if self.config and self.config.has_option(CONFIG_SECTION, name):
            return self.__convert(self.config.get(CONFIG_SECTION, name), default_val)

        # 5) provider variables
        if self.mapping and name in self.mapping:
            env_key = self.mapping[name]
            if env_key and isinstance(env_key, str) and env_key in self.upcased_environ:
                return self.__convert(self.upcased_environ[env_key], default_val)

        # 6) defaults
        return default_val

    def __convert(self, val, default_val):
        if isinstance(val, str) and isinstance(default_val, int) and val.isdigit():
            return int(val)
        return val


class StaticSettings():

    def client_name(self):
        return 'pytest-conquer'

    def client_version(self):
        return __version__

    def platform_name(self):
        return 'python'

    def platform_version(self):
        return platform.python_version()

    def system_cpus(self):
        return psutil.cpu_count()

    def system_os_name(self):
        return platform.system()

    def system_os_version(self):
        return platform.release()

    def system_ram(self):
        return psutil.virtual_memory().total

    def runner_args(self):
        return sys.argv


class DefaultSettings():

    def api_retries(self):
        return 6

    def api_retry_cap(self):
        return 60

    def api_timeout(self):
        return 10

    def api_url(self):
        return 'https://scheduler.testandconquer.com'

    def api_url_fallback(self):
        return 'https://scheduler.testconquer.com'

    def build_dir(self):
        return os.getcwd()

    def build_node(self):
        return str(uuid.uuid4())

    def build_pool(self):
        return 0

    def client_capabilities(self):
        return [
            Capability.Fixtures,
            Capability.IsolatedProcess,
            Capability.LifecycleTimings,
            Capability.SplitByFile,
        ]

    def system_context(self):
        res = {}
        if hasattr(self, 'mapping'):
            for key in self.mapping.get('system_context', {}):
                if key.upper() in self.upcased_environ:
                    res[key] = self.upcased_environ[key.upper()]
        return res

    def system_provider(self):
        return 'custom'

    def vcs_branch(self, cwd=None):
        return Git.branch(cwd)

    def vcs_repo(self, cwd=None):
        return Git.repo(cwd)

    def vcs_revision(self, cwd=None):
        return Git.revision(cwd)

    def vcs_revision_message(self, cwd=None):
        return Git.revision_message(cwd)

    def vcs_type(self):
        return 'git'

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
        self.config_file = None
        self.mapping = None
        self.static_settings = StaticSettings()
        self.default_settings = DefaultSettings()
        self.upcased_environ = dict()
        for key in os.environ:
            upper_key = key.upper()
            upper_key_without_prefix = upper_key.replace(ENV_PREFIX, '', 1)
            if upper_key.startswith(ENV_PREFIX) and not hasattr(self.default_settings, upper_key_without_prefix.lower()):
                raise ValueError("unsupported key '" + key + "' in environment variables")
            self.upcased_environ[upper_key_without_prefix] = os.environ[key]

    def init_from_file(self, path):
        self.config_file = configparser.ConfigParser()
        self.config_file.read(path)  # ignores non-existing file

        if self.config_file.has_section(CONFIG_SECTION):
            for key in self.config_file[CONFIG_SECTION]:
                if not hasattr(self.default_settings, key):
                    raise ValueError("unsupported key '" + key + "' in config file " + path)

        if self.debug is True:
            debug_logger()

    def init_from_server(self, custom_client=None):
        # we need to get the env variable mappings from the server first
        config = (custom_client or Client(self)).get('/config')
        self.__init_mapping(config['envs'])

    def __init_mapping(self, envs):
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

    @property
    def client_workers(self):
        val = self.__getattr__('workers')
        if val == 'max':
            return multiprocessing.cpu_count()
        return val

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
        arg_val = self.args.get(name, None)
        if arg_val is not None:
            return self.__convert(arg_val, default_val)

        # 3) environment variables
        env_name = name.upper()
        if env_name in self.upcased_environ:
            return self.__convert(self.upcased_environ[env_name], default_val)

        # 4) local config file
        if self.config_file and self.config_file.has_option(CONFIG_SECTION, name):
            return self.__convert(self.config_file.get(CONFIG_SECTION, name), default_val)

        # 5) provider variables
        if self.mapping and name in self.mapping:
            env_key = self.mapping[name].upper()
            if env_key and isinstance(env_key, str) and env_key in self.upcased_environ:
                return self.__convert(self.upcased_environ[env_key], default_val)

        # 6) defaults
        if isinstance(default_val, Exception):
            raise default_val
        return default_val

    def __convert(self, val, default_val):
        if isinstance(val, str) and isinstance(default_val, int) and val.isdigit():
            return int(val)
        if isinstance(val, str) and isinstance(default_val, bool):
            return val.lower() == 'true'
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

    def api_key(self):
        return ValueError("missing API key, please set 'api_key'")

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

    def build_id(self):
        return ValueError("missing build ID, please set 'build_id'")

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

    def debug(self):
        return False

    def enabled(self):
        return False

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
        res = Git.branch(cwd)
        if res:
            return res
        return ValueError("missing repository branch, please set 'vcs_branch'")

    def vcs_repo(self, cwd=None):
        return Git.repo(cwd)

    def vcs_revision(self, cwd=None):
        res = Git.revision(cwd)
        if res:
            return res
        return ValueError("missing repository revision, please set 'vcs_revision'")

    def vcs_revision_message(self, cwd=None):
        return Git.revision_message(cwd)

    def vcs_type(self):
        return 'git'

    def workers(self):
        return 1

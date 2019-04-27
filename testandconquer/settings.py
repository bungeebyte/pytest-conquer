import configparser
import multiprocessing
import os
import platform
import sys

import psutil

from enum import Enum
from testandconquer import __version__


class Capability(Enum):
    Fixtures = 'fixtures'
    IsolatedProcess = 'isolated_process'
    LifecycleTimings = 'lifecycle_timings'
    SplitByFile = 'split_by_file'


class Settings():
    def __init__(self, env, cmd_args={}):
        self.env = env
        self.cmd_args = cmd_args

        self.config = configparser.ConfigParser()
        self.config.read('pytest.ini')

        self.api_key = self.__parse('api_key')
        self.api_retries = self.__parse_int('api_retries', 6)
        self.api_retry_cap = self.__parse_int('api_retry_cap', 60)
        self.api_timeout = self.__parse_int('api_timeout', 10)
        self.api_urls = self.__parse('api_url', ['https://scheduler.testandconquer.com', 'https://scheduler.testconquer.com'])
        if not isinstance(self.api_urls, list):
            self.api_urls = [self.api_urls]

        self.build_dir = self.__parse('build_dir', os.getcwd())
        self.build_id = self.__parse('build_id')
        self.build_job = self.__parse('build_job')
        self.build_node = self.__parse('build_node')
        self.build_pool = self.__parse_int('build_pool', 0)
        self.build_project = self.__parse('build_project')
        self.build_url = self.__parse('build_url')

        self.client_capabilities = [
            Capability.Fixtures,
            Capability.IsolatedProcess,
            Capability.LifecycleTimings,
            Capability.SplitByFile,
        ]
        self.client_name = 'python-official'
        self.client_version = __version__

        self.platform_name = 'python'
        self.platform_version = platform.python_version()
        if env.python_version() < (3, 4):
            raise SystemExit('Sorry, testandconquer requires at least Python 3.4\n')

        if self.__parse('workers', '').lower() == 'max':
            self.plugin_workers = multiprocessing.cpu_count()
        else:
            self.plugin_workers = self.__parse_int('workers', 1)

        self.runner_args = sys.argv
        self.runner_name = None
        self.runner_plugins = set()
        self.runner_root = None
        self.runner_version = None

        self.system_name = self.env.name()
        self.system_context = self.env.context()
        self.system_cpus = psutil.cpu_count()
        self.system_os_name = platform.system()
        self.system_os_version = platform.release()
        self.system_ram = psutil.virtual_memory().total

        self.vcs_branch = self.__parse('vcs_branch')
        self.vcs_pr = self.__parse('vcs_pr')
        self.vcs_repo = self.__parse('vcs_repo')
        self.vcs_revision = self.__parse('vcs_revision')
        self.vcs_revision_message = self.__parse('vcs_revision_message')
        self.vcs_tag = self.__parse('vcs_tag')
        self.vcs_type = self.__parse('vcs_type')

    def plugin_enabled(self):
        return True  # TODO

    def __parse(self, name, default=None):
        return self.env.get(name) or \
            self.config.get('conquer', name, fallback=None) or \
            self.cmd_args.get(name, None) or \
            default

    def __parse_int(self, name, default=None):
        val = self.__parse(name, default)
        try:
            return int(val)
        except ValueError:
            raise ValueError('config parameter "' + name + '" must be an integer, but is "' + val + "'")

    def validate(self):
        if self.api_key is None:
            raise ValueError("missing API key, please set 'api_key'")
        if self.build_id is None:
            raise ValueError("missing build ID, please set 'build_id'")
        if self.vcs_branch is None:
            raise ValueError("missing repository branch, please set 'vcs_branch'")
        if self.vcs_revision is None:
            raise ValueError("missing repository revision, please set 'vcs_revision'")

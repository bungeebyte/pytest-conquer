import configparser
import os
import platform
import sys

import psutil

from enum import Enum
from maketestsgofaster import __version__


class Capability(Enum):
    Fixtures = 'fixtures'
    LifecycleTimings = 'lifecycle_timings'
    SplitByFile = 'split_by_file'


class Settings():
    def __init__(self, env):
        self.env = env

        self.config = configparser.ConfigParser()
        self.config.read('pytest.ini')

        self.api_key = self.__parse('api', 'key')
        self.api_retries = int(self.__parse('api', 'retries', 6))
        self.api_retry_cap = float(self.__parse('api', 'retry_cap', 60))
        self.api_timeout = float(self.__parse('api', 'timeout', 10))
        self.api_urls = self.__parse('api', 'url', ['https://scheduler.maketestsgofaster.com', 'https://scheduler.maketestsgofaster.co'])
        if not isinstance(self.api_urls, list):
            self.api_urls = [self.api_urls]

        self.build_dir = self.__parse('build', 'dir', os.getcwd())
        self.build_id = self.__parse('build', 'id')
        self.build_job = self.__parse('build', 'job')
        self.build_pool = int(self.__parse('build', 'pool', 0))
        self.build_project = self.__parse('build', 'project')
        self.build_url = self.__parse('build', 'url')
        self.build_worker = self.__parse('build', 'worker')

        self.client_capabilities = []
        self.client_name = 'python-official'
        self.client_version = __version__

        self.platform_name = 'python'
        self.platform_version = platform.python_version()
        if env.python_version() < (3, 4):
            raise SystemExit('Sorry, maketestsgofaster requires at least Python 3.4\n')

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

        self.vcs_branch = self.__parse('vcs', 'branch')
        self.vcs_pr = self.__parse('vcs', 'pr')
        self.vcs_repo = self.__parse('vcs', 'repo')
        self.vcs_revision = self.__parse('vcs', 'revision')
        self.vcs_revision_message = self.__parse('vcs', 'revision_message')
        self.vcs_tag = self.__parse('vcs', 'tag')
        self.vcs_type = self.__parse('vcs', 'type')

    def __parse(self, prefix, name, default=None):
        full_name = prefix + '_' + name
        return self.env.get(full_name) or \
            self.config.get("maketestsgofaster", full_name, fallback=None) or \
            default

    def validate(self):
        if self.api_key is None:
            raise RuntimeError("missing API key, please set 'api_key'")
        if self.build_id is None:
            raise RuntimeError("missing build ID, please set 'build_id'")
        if self.vcs_branch is None:
            raise RuntimeError("missing repository branch, please set 'vcs_branch'")
        if self.vcs_revision is None:
            raise RuntimeError("missing repository revision, please set 'vcs_revision'")

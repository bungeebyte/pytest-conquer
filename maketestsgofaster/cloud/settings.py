import os
import platform

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

        self.api_key = self.__parse('api_key')
        self.api_retries = int(self.__parse('api_retries', 5))
        self.api_timeout = int(self.__parse('api_timeout', 60))
        self.api_urls = self.__parse('api_url', ['https://scheduler.maketestsgofaster.com', 'https://scheduler.maketestsgofaster.co'])
        if not isinstance(self.api_urls, list):
            self.api_urls = [self.api_urls]

        self.build_dir = self.__parse('build_dir', os.getcwd())
        self.build_id = self.__parse('build_id')
        self.build_pool = int(self.__parse('build_pool', 1))
        self.build_project = self.__parse('build_project')
        self.build_url = self.__parse('build_url')
        self.build_worker = self.__parse('build_worker')

        self.client_capabilities = []
        self.client_name = 'python-official'
        self.client_version = __version__

        self.platform_name = 'python'
        self.platform_version = platform.python_version()
        if env.python_version() < (3, 4):
            raise SystemExit('Sorry, maketestsgofaster requires at least Python 3.4\n')

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
        self.vcs_pr = self.__parse('vsc_pr')
        self.vcs_repo = self.__parse('vcs_repo')
        self.vcs_revision = self.__parse('vcs_revision')
        self.vcs_revision_message = self.__parse('vcs_revision_message')
        self.vcs_tag = self.__parse('vcs_tag')
        self.vcs_type = self.__parse('vcs_type')

    def __parse(self, name, default=None):
        return self.env.get(name) or default

    def validate(self):
        if self.api_key is None:
            raise RuntimeError("missing API key, please set 'api_key'")
        if self.build_id is None:
            raise RuntimeError("missing build ID, please set 'build_id'")
        if self.vcs_branch is None:
            raise RuntimeError("missing repository branch, please set 'vcs_branch'")
        if self.vcs_revision is None:
            raise RuntimeError("missing repository revision, please set 'vcs_revision'")

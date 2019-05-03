import configparser
import os
import uuid
import sys

from testandconquer.git import Git
from testandconquer.client import Client


CONFIG_SECTION = 'conquer'
ENV_PREFIX = 'CONQUER_'


class Env:

    def __init__(self, args={}):
        self.args = args
        self.config = configparser.ConfigParser()
        self.config.read('pytest.ini')
        self.mapping = {}
        self.upcased_environ = dict()
        for key in os.environ:
            self.upcased_environ[key.upper()] = os.environ[key]

    def init_mapping(self, settings):
        envs = Client(settings).get('/envs')
        for env in envs:
            is_match = True
            for condition in env['conditions']:
                if condition not in self.upcased_environ:
                    is_match = False
                    break
            if is_match:
                self.mapping = env['mapping']
                self.mapping['system_provider'] = env['name']
                break

    def get(self, name):
        # 1) plugin arguments
        if name in self.args:
            return self.args.get(name)

        # 2) environment variables
        env_name = (ENV_PREFIX + name).upper()
        if env_name in self.upcased_environ:
            return self.upcased_environ[env_name]

        # 3) local config file
        if self.config.has_option(CONFIG_SECTION, name):
            return self.config.get(CONFIG_SECTION, name)

        # 4) provider variables
        if name in self.mapping:
            env_key = self.mapping[name]
            if env_key in self.upcased_environ:
                return self.upcased_environ[env_key]

        # 5) defaults
        method = getattr(self, name, None)
        if method:
            return method()

    # Defaults:

    def build_dir(self):
        return os.getcwd()

    def build_node(self):
        return str(uuid.uuid4())

    def python_version(self):
        return sys.version_info

    def system_context(self):
        res = {}
        if self.mapping:
            for key in self.mapping['build_context']:
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

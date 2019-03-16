import pkgutil
import os
import uuid
import sys

from maketestsgofaster import logger
from maketestsgofaster.git import Git


ENV_PREFIX = 'MTGF_'


class Env:

    @staticmethod
    def create(overrides={}):
        # make sure all classes are loaded first
        for imp, module, ispackage in pkgutil.walk_packages(path=pkgutil.extend_path(__path__, __name__), prefix=__name__ + '.'):
            __import__(module)

        env = Custom(overrides)
        for env_cls in Env.__subclasses__():
            inst = env_cls(overrides)
            if inst.active():
                logger.debug('[env] recognized environment as "%s"', inst.name())
                env = inst
                break
        return env

    def __init__(self, overrides):
        self.overrides = overrides

    def get(self, var):
        if var in self.overrides:
            return self.overrides[var]

        env_var_name = (ENV_PREFIX + var).upper()
        for key in os.environ:
            if key.upper() == env_var_name:
                return os.environ[key]

        method = getattr(self, var, None)
        if method:
            return method()

    def get_all(*names):
        res = {}
        for key in os.environ:
            if key in names:
                res[key] = os.environ[key]
        return res

    # Defaults:

    def build_dir(self):
        return os.getcwd()

    def build_node(self):
        return str(uuid.uuid4())

    def context(self):
        return {}

    def python_version(self):
        return sys.version_info

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


class Custom(Env):

    def active(self):
        return False

    def name(self):
        return 'custom'

import pkgutil
import os
import subprocess
import uuid
import sys

from maketestsgofaster import logger


try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

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
        if env_var_name in os.environ:
            return os.environ[env_var_name]

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

    def build_worker(self):
        return str(uuid.uuid4())

    def context(self):
        return {}

    def python_version(self):
        return sys.version_info

    def vcs_branch(self):
        try:
            subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=DEVNULL).strip()
        except subprocess.CalledProcessError:
            return None

    def vcs_repo(self):
        try:
            subprocess.check_output(['git', 'config', '--get', 'remove.origin.url'], stderr=DEVNULL).strip()
        except subprocess.CalledProcessError:
            return None

    def vcs_revision(self):
        try:
            subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=DEVNULL).strip()
        except subprocess.CalledProcessError:
            return None

    def vcs_revision_message(self):
        try:
            subprocess.check_output(['git', 'log', '-1', '--pretty=%B'], stderr=DEVNULL).strip()
        except subprocess.CalledProcessError:
            return None

    def vcs_type(self):
        'git'


class Custom(Env):

    def active(self):
        False

    def name(self):
        return 'custom'

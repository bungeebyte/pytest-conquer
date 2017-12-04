import os

from maketestsgofaster.cloud.env import Env


# https://semaphoreci.com/docs/available-environment-variables.html
class Semaphore(Env):
    def active(self):
        return 'CI' in os.environ and 'SEMAPHORE' in os.environ

    def name(self):
        return 'semaphore'

    def context(self):
        return self.get_all(
            'SEMAPHORE_CURRENT_JOB',
            'SEMAPHORE_JOB_COUNT',
            'SEMAPHORE_TRIGGER_SOURCE')

    def build_id(self):
        return os.environ.get('SEMAPHORE_BUILD_NUMBER')

    def build_pool(self):
        return os.environ.get('SEMAPHORE_THREAD_COUNT')

    def build_worker(self):
        return os.environ.get('SEMAPHORE_CURRENT_THREAD')

    def vcs_branch(self):
        return os.environ.get('BRANCH_NAME')

    def vcs_pr(self):
        return os.environ.get('PULL_REQUEST_NUMBER')

    def vcs_revision(self):
        return os.environ.get('REVISION')

import os

from testandconquer.env import Env


# http://devcenter.wercker.com/docs/environment-variables/available-env-vars
class Wercker(Env):
    def active(self):
        return 'CI' in os.environ and 'WERCKER_GIT_BRANCH' in os.environ

    def name(self):
        return 'wercker'

    def context(self):
        return self.get_all(
            'WERCKER_APPLICATION_URL')

    def build_id(self):
        return os.environ.get('WERCKER_MAIN_PIPELINE_STARTED')

    def build_url(self):
        return os.environ.get('WERCKER_RUN_URL')

    def vcs_branch(self):
        return os.environ.get('WERCKER_GIT_BRANCH')

    def vcs_revision(self):
        return os.environ.get('WERCKER_GIT_COMMIT')

import os

from maketestsgofaster.cloud.env import Env


# https://circleci.com/docs/2.0/env-vars/#circleci-built-in-environment-variables
# https://circleci.com/docs/1.0/environment-variables/
class Circle(Env):
    def active(self):
        return 'CI' in os.environ and 'CIRCLECI' in os.environ

    def name(self):
        return 'circle'

    def context(self):
        return self.get_all(
            'CIRCLE_STAGE')

    def build_id(self):
        return os.environ.get('CIRCLE_BUILD_NUM')

    def build_job(self):
        return os.environ.get('CIRCLE_JOB')

    def build_url(self):
        return os.environ.get('CIRCLE_BUILD_URL')

    def build_pool(self):
        return os.environ.get('CIRCLE_NODE_TOTAL')

    def build_worker(self):
        return os.environ.get('CIRCLE_NODE_INDEX')

    def vcs_branch(self):
        return os.environ.get('CIRCLE_BRANCH')

    def vcs_pr(self):
        return os.environ.get('CIRCLE_PR_NUMBER')

    def vcs_repo(self):
        return os.environ.get('CIRCLE_REPOSITORY_URL')

    def vcs_revision(self):
        return os.environ.get('CIRCLE_SHA1')

    def vcs_tag(self):
        return os.environ.get('CIRCLE_TAG')

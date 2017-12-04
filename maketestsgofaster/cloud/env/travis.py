import os

from maketestsgofaster.cloud.env import Env


# https://docs.travis-ci.com/user/environment-variables/#Default-Environment-Variables
class Travis(Env):
    def active(self):
        return 'CI' in os.environ \
            and 'TRAVIS' in os.environ \
            and 'SHIPPABLE' not in os.environ

    def name(self):
        return 'travis'

    def context(self):
        return self.get_all(
            'TRAVIS_EVENT_TYPE')

    def build_id(self):
        return os.environ.get('TRAVIS_BUILD_NUMBER')

    def build_project(self):
        return os.environ.get('TRAVIS_REPO_SLUG')

    def build_worker(self):
        return os.environ.get('TRAVIS_JOB_NUMBER')

    def vcs_branch(self):
        if os.environ.get('TRAVIS_PULL_REQUEST') == 'false':
            return os.environ.get('TRAVIS_BRANCH')
        else:
            return os.environ.get('TRAVIS_PULL_REQUEST_BRANCH')

    def vcs_pr(self):
        pr = os.environ.get('TRAVIS_PULL_REQUEST')
        if pr == 'false':
            return None
        else:
            return pr

    def vcs_revision(self):
        return os.environ.get('TRAVIS_COMMIT')

    def vcs_revision_message(self):
        return os.environ.get('TRAVIS_COMMIT_MESSAGE')

    def vcs_tag(self):
        return os.environ.get('TRAVIS_TAG')

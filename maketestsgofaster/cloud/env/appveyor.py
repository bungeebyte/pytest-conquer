import os

from maketestsgofaster.cloud.env import Env


# https://www.appveyor.com/docs/environment-variables/
class AppVeyor(Env):
    def active(self):
        return 'CI' in os.environ and 'APPVEYOR' in os.environ

    def name(self):
        return 'appveyor'

    def context(self):
        return self.get_all(
            'APPVEYOR_RE_BUILD')

    def build_id(self):
        return os.environ.get('APPVEYOR_BUILD_ID')

    def build_project(self):
        return os.environ.get('APPVEYOR_PROJECT_SLUG')

    def build_worker(self):
        return os.environ.get('APPVEYOR_JOB_NUMBER')

    def vcs_branch(self):
        return os.environ.get('APPVEYOR_REPO_BRANCH')

    def vcs_pr(self):
        return os.environ.get('APPVEYOR_PULL_REQUEST_NUMBER')

    def vcs_revision(self):
        return os.environ.get('APPVEYOR_REPO_COMMIT')

    def vcs_revision_message(self):
        return os.environ.get('APPVEYOR_REPO_COMMIT_MESSAGE')

    def vcs_tag(self):
        return os.environ.get('APPVEYOR_REPO_TAG_NAME')

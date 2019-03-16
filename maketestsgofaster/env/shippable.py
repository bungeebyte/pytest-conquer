import os

from maketestsgofaster.env import Env


# http://docs.shippable.com/ci/env-vars/
class Shippable(Env):
    def active(self):
        return 'CI' in os.environ and 'SHIPPABLE' in os.environ

    def name(self):
        return 'shippable'

    def context(self):
        return self.get_all(
            'PROJECT_ID')

    def build_id(self):
        return os.environ.get('BUILD_NUMBER')

    def build_url(self):
        return os.environ.get('BUILD_URL')

    def build_node(self):
        return os.environ.get('JOB_NUMBER')

    def vcs_branch(self):
        return os.environ.get('BRANCH')

    def vcs_pr(self):
        if os.environ.get('IS_PULL_REQUEST') == 'true':
            return os.environ.get('PULL_REQUEST')

    def vcs_repo(self):
        return os.environ.get('REPOSITORY_URL')

    def vcs_revision(self):
        return os.environ.get('COMMIT')

    def vcs_revision_message(self):
        return os.environ.get('COMMIT_MESSAGE')

    def vcs_tag(self):
        if os.environ.get('IS_GIT_TAG') == 'true':
            return os.environ.get('GIT_TAG_NAME')

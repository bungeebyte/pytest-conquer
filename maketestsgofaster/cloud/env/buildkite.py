import os

from maketestsgofaster.cloud.env import Env


# https://buildkite.com/docs/guides/environment-variables
class Buildkite(Env):
    def active(self):
        return 'CI' in os.environ and 'BUILDKITE' in os.environ

    def name(self):
        return 'buildkite'

    def context(self):
        return self.get_all(
            'BUILDKITE_AGENT_NAME',
            'BUILDKITE_COMMAND')

    def build_id(self):
        return os.environ.get('BUILDKITE_BUILD_NUMBER')

    def build_url(self):
        return os.environ.get('BUILDKITE_BUILD_URL')

    def build_pool(self):
        return os.environ.get('BUILDKITE_PARALLEL_JOB_COUNT')

    def build_worker(self):
        return os.environ.get('BUILDKITE_PARALLEL_JOB')

    def vcs_branch(self):
        return os.environ.get('BUILDKITE_BRANCH')

    def vcs_repo(self):
        return os.environ.get('BUILDKITE_REPO')

    def vcs_revision(self):
        return os.environ.get('BUILDKITE_COMMIT')

    def vcs_revision_message(self):
        return os.environ.get('BUILDKITE_MESSAGE')

    def vcs_tag(self):
        return os.environ.get('BUILDKITE_TAG')

import os

from testandconquer.env import Env


# https://docs.gitlab.com/ee/ci/variables/
class GitLab(Env):
    def active(self):
        return 'CI' in os.environ and 'GITLAB_CI' in os.environ

    def name(self):
        return 'gitlab'

    def context(self):
        return self.get_all(
            'CI_RUNNER_REVISION',
            'CI_RUNNER_VERSION',
            'CI_SERVER_REVISION',
            'CI_SERVER_VERSION')

    def build_id(self):
        return os.environ.get('CI_JOB_NAME') or os.environ.get('CI_BUILD_NAME')

    def build_job(self):
        return os.environ.get('CI_JOB_STAGE') or os.environ.get('CI_BUILD_STAGE')

    def build_node(self):
        return os.environ.get('CI_RUNNER_ID')

    def vcs_branch(self):
        return os.environ.get('CI_COMMIT_REF_NAME') or os.environ.get('CI_BUILD_REF_NAME')

    def vcs_repo(self):
        return os.environ.get('CI_REPOSITORY_URL')

    def vcs_revision(self):
        return os.environ.get('CI_COMMIT_SHA') or os.environ.get('CI_BUILD_REF')

    def vcs_tag(self):
        return os.environ.get('CI_COMMIT_TAG') or os.environ.get('CI_BUILD_TAG')

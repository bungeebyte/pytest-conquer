import os

from maketestsgofaster.env import Env


# https://documentation.codeship.com/basic/builds-and-configuration/set-environment-variables/#default-environment-variables
# https://documentation.codeship.com/pro/builds-and-configuration/environment-variables/#default-environment-variables
class Codeship(Env):
    def active(self):
        return 'CI_NAME' in os.environ and os.environ['CI_NAME'] == 'codeship'

    def name(self):
        return 'codeship'

    def context(self):
        return self.get_all(
            'CI_PROJECT_ID',
        )

    def build_id(self):
        return os.environ.get('CI_BUILD_NUMBER') or os.environ.get('CI_BUILD_ID')

    def build_url(self):
        return os.environ.get('CI_BUILD_URL')

    def vcs_branch(self):
        return os.environ.get('CI_BRANCH')

    def vcs_revision(self):
        return os.environ.get('CI_COMMIT_ID')

    def vcs_revision_message(self):
        return os.environ.get('CI_MESSAGE') or os.environ.get('CI_COMMIT_MESSAGE')

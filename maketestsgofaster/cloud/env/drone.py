import os

from maketestsgofaster.cloud.env import Env


# https://docs.drone.io/reference/environ/
class Drone(Env):
    def active(self):
        return 'CI' in os.environ and 'DRONE' in os.environ

    def name(self):
        return 'drone'

    def context(self):
        return self.get_all()

    def build_id(self):
        return os.environ.get('DRONE_BUILD_NUMBER')

    def build_url(self):
        return os.environ.get('DRONE_BUILD_LINK')

    def build_node(self):
        return os.environ.get('DRONE_JOB_NUMBER')

    def vcs_branch(self):
        return os.environ.get('DRONE_COMMIT_BRANCH')

    def vcs_pr(self):
        return os.environ.get('DRONE_PULL_REQUEST')

    def vcs_repo(self):
        return os.environ.get('DRONE_REPO_LINK')

    def vcs_revision(self):
        return os.environ.get('DRONE_COMMIT_SHA')

    def vcs_tag(self):
        return os.environ.get('DRONE_TAG')

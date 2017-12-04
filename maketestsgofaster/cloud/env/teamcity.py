import os

from maketestsgofaster.cloud.env import Env


# https://confluence.jetbrains.com/display/TCD10/Predefined+Build+Parameters
class TeamCity(Env):
    def active(self):
        return 'CI' in os.environ and 'TEAMCITY_VERSION' in os.environ

    def name(self):
        return 'teamcity'

    def context(self):
        return self.get_all(
            'TEAMCITY_VERSION')

    def build_id(self):
        return os.environ.get('BUILD_NUMBER')

    def build_project(self):
        return os.environ.get('TEAMCITY_PROJECT_NAME')

    def vcs_revision(self):
        return os.environ.get('BUILD_VCS_NUMBER')

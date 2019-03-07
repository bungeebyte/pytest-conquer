import os

from maketestsgofaster.cloud.env import Env


# https://confluence.atlassian.com/bamboo/bamboo-variables-289277087.html
class Bamboo(Env):
    def active(self):
        return 'CI' in os.environ and 'bamboo.buildKey' in os.environ

    def name(self):
        return 'bamboo'

    def context(self):
        return self.get_all(
            'bamboo.buildKey')

    def build_id(self):
        return os.environ.get('bamboo.buildNumber')

    def build_project(self):
        return os.environ.get('bamboo.planKey')

    def build_url(self):
        return os.environ.get('bamboo.buildResultsUrl') or os.environ.get('bamboo.resultsUrl')

    def build_worker(self):
        return os.environ.get('bamboo.shortJobKey')

    def vcs_branch(self):
        return os.environ.get('bamboo.planRepository.branch')

    def vcs_repo(self):
        return os.environ.get('bamboo.planRepository.repositoryUrl')

    def vcs_revision(self):
        return os.environ.get('bamboo.planRepository.revision')

    def vcs_type(self):
        return os.environ.get('bamboo.planRepository.type')

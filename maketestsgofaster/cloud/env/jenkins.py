import os

from maketestsgofaster.cloud.env import Env


# https://wiki.jenkins.io/display/JENKINS/Building+a+software+project#Buildingasoftwareproject-belowJenkinsSetEnvironmentVariables
class Jenkins(Env):
    def active(self):
        return 'JENKINS_URL' in os.environ

    def name(self):
        return 'jenkins'

    def context(self):
        return self.get_all(
            'JOB_NAME',
            'NODE_NAME')

    def build_id(self):
        return os.environ.get('BUILD_NUMBER')

    def build_url(self):
        return os.environ.get('BUILD_URL')

    def build_worker(self):
        return os.environ.get('EXECUTOR_NUMBER')

    def vcs_branch(self):
        return os.environ.get('GIT_BRANCH')

    def vcs_revision(self):
        return os.environ.get('GIT_COMMIT')

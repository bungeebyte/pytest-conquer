import os
import subprocess

try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


class Git:

    @staticmethod
    def branch(cwd):
        return Git.exec(['rev-parse', '--abbrev-ref', 'HEAD'], cwd)

    @staticmethod
    def repo(cwd):
        return Git.exec(['config', '--get', 'remote.origin.url'], cwd)

    @staticmethod
    def revision(cwd):
        return Git.exec(['rev-parse', 'HEAD'], cwd)

    @staticmethod
    def revision_message(cwd):
        return Git.exec(['log', '-1', '--pretty=%B'], cwd)

    @staticmethod
    def exec(args, cwd):
        try:
            return str(subprocess.check_output(['git'] + args, cwd=cwd or os.getcwd()).strip())
        except subprocess.CalledProcessError:
            return None

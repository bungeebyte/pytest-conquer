import os

from maketestsgofaster.cloud.env import Custom, Env


def test_create():
    env = Env.create()

    assert env.name() is 'custom'
    assert type(env) is Custom

    assert env.active() is False
    assert env.build_dir()
    assert env.build_node()

    # uses `git`
    cwd = os.path.dirname(os.path.realpath(__file__))  # by default tox runs test in a tmp dir
    assert env.vcs_branch(cwd)
    assert env.vcs_repo(cwd)
    assert env.vcs_revision(cwd)
    assert env.vcs_revision_message(cwd)
    assert env.vcs_type() is 'git'

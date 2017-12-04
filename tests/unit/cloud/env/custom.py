from maketestsgofaster.cloud.env import Custom, Env


def test_create():
    env = Env.create()
    assert env.name() is 'custom'
    assert type(env) is Custom

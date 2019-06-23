from testandconquer.settings import Settings


class MockSettings(Settings):
    def __init__(self, args):
        args['build_id'] = args.get('build_id', 'ID')
        args['vcs_branch'] = args.get('vcs_branch', 'BRANCH')
        args['vcs_revision'] = args.get('vcs_revision', 'REVISION')
        super().__init__(args)

    # skips network call
    def init_provider(self, _client=None):
        pass

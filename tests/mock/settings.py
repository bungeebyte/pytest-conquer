from testandconquer.settings import Settings


class MockSettings(Settings):
    def __init__(self, args):
        args['api_key'] = args.get('api_key', 'some-api-key')
        args['api_retry_cap'] = args.get('api_retry_cap', '1')
        args['build_id'] = args.get('build_id', 'ID')
        args['system_provider'] = args.get('system_provider', 'provider')
        args['vcs_branch'] = args.get('vcs_branch', 'BRANCH')
        args['vcs_revision'] = args.get('vcs_revision', 'REVISION')
        super().__init__(args)

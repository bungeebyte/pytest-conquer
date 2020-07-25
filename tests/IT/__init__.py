import os

import testandconquer


def run_test(pyt, files, args=['--conquer']):
    source_by_name = {}
    here = os.path.abspath(os.path.dirname(__file__))
    files.append('fixtures/conftest.py')
    files.append('fixtures/fixture.py')
    files.append('fixtures/lib.py')
    for file in files:
        with open(os.path.join(here, file)) as f:
            source_by_name[file] = f.readlines()
    pyt.makepyfile(**source_by_name)
    test_result = pyt.runpytest('-s', *args)
    return (test_result, testandconquer.plugin.scheduler or None)


def assert_outcomes(result, passed=0, skipped=0, failed=0, error=0):
    d = result.parseoutcomes()
    obtained = {
        'passed': d.get('passed', 0),
        'skipped': d.get('skipped', 0),
        'failed': d.get('failed', 0),
        'error': d.get('error', 0),
    }
    assert obtained == dict(passed=passed, skipped=skipped, failed=failed, error=error), obtained

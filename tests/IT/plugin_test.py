import os
import os.path

import pytest

import maketestsgofaster.scheduler
from maketestsgofaster.model import Failure, Location, ReportItem, SuiteItem

from tests.IT.mock.scheduler import MockScheduler


def test_function_pass(testdir):
    test_file = 'fixtures/test_function_pass.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, 'test_pass', 1), 'passed'),
    ]


def test_function_fail(testdir):
    test_file = 'fixtures/test_function_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, failed=1)

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, 'test_fail', 1), 'failed',
                   Failure('AssertionError', 'assert (2 + 2) == 22')),
    ]


def test_function_skip(testdir):
    test_file = 'fixtures/test_function_skip.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, skipped=1)

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, 'test_skip', 4), 'skipped'),
    ]


def test_function_xfail(testdir):
    test_file = 'fixtures/test_function_xfail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=0)

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, 'test_xfail', 4), 'skipped',
                   Failure('AssertionError', 'assert (1 + 2) == 12')),
    ]


def test_function_setup(testdir):
    test_file = 'fixtures/test_function_setup.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('setup', Location(test_file, 'setup_function', 1), 42, []),
        SuiteItem('test', Location(test_file, 'test', 5), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'setup_function', 1), 'passed'),
        ReportItem('test', Location(test_file, 'test', 5), 'passed'),
    ]


def test_function_setup_fail(testdir):
    test_file = 'fixtures/test_function_setup_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'setup_function', 1), 'failed',
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, 'test', 5), 'failed'),
    ]


def test_function_teardown(testdir):
    test_file = 'fixtures/test_function_teardown.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('teardown', Location(test_file, 'teardown_function', 1), 42, []),
        SuiteItem('test', Location(test_file, 'test', 5), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, 'teardown_function', 1), 'passed'),
        ReportItem('test', Location(test_file, 'test', 5), 'passed'),
    ]


def test_function_teardown_fail(testdir):
    test_file = 'fixtures/test_function_teardown_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, 'teardown_function', 1), 'failed',
                   Failure('Exception', 'teardown failed')),
        ReportItem('test', Location(test_file, 'test', 5), 'passed'),
    ]


def test_function_parameterized(testdir):
    test_file = 'fixtures/test_function_param.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=3)

    assert scheduler.suite_items == [
        SuiteItem('test', Location(test_file, 'test_param[2+4-6]', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test_param[3+5-8]', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test_param[6*9-54]', 4), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, 'test_param[2+4-6]', 4), 'passed'),
        ReportItem('test', Location(test_file, 'test_param[3+5-8]', 4), 'passed'),
        ReportItem('test', Location(test_file, 'test_param[6*9-54]', 4), 'passed'),
    ]


def test_module_setup(testdir):
    test_file = 'fixtures/test_module_setup.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert scheduler.suite_items == [
        SuiteItem('setup', Location(test_file, 'setup_module', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test1', 9), 42, []),
        SuiteItem('test', Location(test_file, 'test2', 14), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'setup_module', 4), 'passed'),
        ReportItem('test', Location(test_file, 'test1', 9), 'passed'),
        ReportItem('test', Location(test_file, 'test2', 14), 'passed'),
    ]


def test_module_setup_fail(testdir):
    test_file = 'fixtures/test_module_setup_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'setup_module', 1), 'failed',
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, 'test', 5), 'failed'),
    ]


def test_module_teardown(testdir):
    test_file = 'fixtures/test_module_teardown.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('teardown', Location(test_file, 'teardown_module', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test', 9), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, 'teardown_module', 4), 'passed'),
        ReportItem('test', Location(test_file, 'test', 9), 'passed'),
    ]


def test_module_teardown_fail(testdir):
    test_file = 'fixtures/test_module_teardown_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, 'teardown_module', 1), 'failed',
                   Failure('Exception', 'teardown failed')),
        ReportItem('test', Location(test_file, 'test', 5), 'passed'),
    ]


def test_fixture(testdir):
    test_file = 'fixtures/test_fixture.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('fixture', Location(test_file, 'fixture', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test_with_fixture', 9), 42, [
            SuiteItem('fixture', Location(test_file, 'fixture', 4), 42, []),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'fixture', 4), 'passed'),
        ReportItem('teardown', Location(test_file, 'fixture', 4), 'passed'),
        ReportItem('test', Location(test_file, 'test_with_fixture', 9), 'passed'),
    ]


def test_fixtures(testdir):
    test_file = 'fixtures/test_fixtures.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('fixture', Location(test_file, 'fixture1', 4), 42, []),
        SuiteItem('fixture', Location(test_file, 'fixture2', 9), 42, []),
        SuiteItem('test', Location(test_file, 'test_with_fixtures', 14), 42, [
            SuiteItem('fixture', Location(test_file, 'fixture1', 4), 42, []),
            SuiteItem('fixture', Location(test_file, 'fixture2', 9), 42, []),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'fixture1', 4), 'passed'),
        ReportItem('setup', Location(test_file, 'fixture2', 9), 'passed'),
        ReportItem('teardown', Location(test_file, 'fixture1', 4), 'passed'),
        ReportItem('teardown', Location(test_file, 'fixture2', 9), 'passed'),
        ReportItem('test', Location(test_file, 'test_with_fixtures', 14), 'passed'),
    ]


def test_fixture_nested(testdir):
    test_file = 'fixtures/test_fixture_nested.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('fixture', Location(test_file, 'fixture1', 4), 42, []),
        SuiteItem('fixture', Location(test_file, 'fixture2', 9), 42, []),
        SuiteItem('test', Location(test_file, 'test_with_fixture', 14), 42, [
            SuiteItem('fixture', Location(test_file, 'fixture1', 4), 42, []),
            SuiteItem('fixture', Location(test_file, 'fixture2', 9), 42, []),
        ]),
    ]

    # note that nested fixtures are evaluated sequentially, one _after_ the other
    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'fixture1', 4), 'passed'),
        ReportItem('setup', Location(test_file, 'fixture2', 9), 'passed'),
        ReportItem('teardown', Location(test_file, 'fixture1', 4), 'passed'),
        ReportItem('teardown', Location(test_file, 'fixture2', 9), 'passed'),
        ReportItem('teardown', Location(test_file, 'fixture2', 9), 'passed'),
        ReportItem('test', Location(test_file, 'test_with_fixture', 14), 'passed'),
    ]


def test_fixture_session(testdir):
    test_file = 'fixtures/test_fixture_session.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('fixture', Location('fixtures/conftest.py', 'fixture_session', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test_with_fixture', 1), 42, [
            SuiteItem('fixture', Location('fixtures/conftest.py', 'fixture_session', 4), 42, []),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location('fixtures/conftest.py', 'fixture_session', 4), 'passed'),
        ReportItem('teardown', Location('fixtures/conftest.py', 'fixture_session', 4), 'passed'),
        ReportItem('test', Location(test_file, 'test_with_fixture', 1), 'passed'),
    ]


def test_fixture_missing(testdir):
    test_file = 'fixtures/test_fixture_missing.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.suite_items == [
        SuiteItem('test', Location(test_file, 'test_with_missing_fixture', 1), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, 'test_with_missing_fixture', 1), 'failed'),
    ]


def test_fixture_import(testdir):
    test_file = 'fixtures/test_fixture_import.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('fixture', Location('fixtures/fixture.py', 'fixture_import', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test_with_fixture', 5), 42, [
            SuiteItem('fixture', Location('fixtures/fixture.py', 'fixture_import', 4), 42, []),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location('fixtures/fixture.py', 'fixture_import', 4), 'passed'),
        ReportItem('teardown', Location('fixtures/fixture.py', 'fixture_import', 4), 'passed'),
        ReportItem('test', Location(test_file, 'test_with_fixture', 5), 'passed'),
    ]


def test_fixture_fail(testdir):
    test_file = 'fixtures/test_fixture_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.suite_items == [
        SuiteItem('fixture', Location(test_file, 'fixture', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test_with_fixture', 9), 42, [
            SuiteItem('fixture', Location(test_file, 'fixture', 4), 42, []),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'fixture', 4), 'error',
                   Failure('Exception', 'setup failed')),
        ReportItem('teardown', Location(test_file, 'fixture', 4), 'passed'),
        ReportItem('test', Location(test_file, 'test_with_fixture', 9), 'failed'),
    ]


def test_multiple_test_files(testdir):
    (result, scheduler) = run_test(testdir, ['fixtures/test_function_fail.py', 'fixtures/test_function_pass.py', 'fixtures/test_function_skip.py'])
    assert_outcomes(result, failed=1, passed=1, skipped=1)

    items = scheduler.report_items
    assert len(items) == 3


def test_class(testdir):
    test_file = 'fixtures/test_class.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('test', Location(test_file, 'TestObject::test', 3), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, 'TestObject::test', 3), 'passed'),
    ]


def test_class_inheritance(testdir):
    (result, scheduler) = run_test(testdir, ['fixtures/test_class_inheritance_1.py', 'fixtures/test_class_inheritance_2.py'])
    assert_outcomes(result, passed=4)

    assert scheduler.suite_items == [
        SuiteItem('setup', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::setup_class', 3), 42, []),
        SuiteItem('setup', Location('fixtures/test_class_inheritance_1.py', 'TestObject2::setup_class', 3), 42, []),
        SuiteItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::teardown_class', 7), 42, []),
        SuiteItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'TestObject2::teardown_class', 7), 42, []),
        SuiteItem('test', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::test1', 11), 42, []),
        SuiteItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject1::test1', 11), 42, []),
        SuiteItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject2::test1', 11), 42, []),
        SuiteItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject2::test2', 6), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::setup_class', 3), 'passed'),
        ReportItem('setup', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::setup_class', 3), 'passed'),
        ReportItem('setup', Location('fixtures/test_class_inheritance_1.py', 'TestObject2::setup_class', 3), 'passed'),
        ReportItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::teardown_class', 7), 'passed'),
        ReportItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::teardown_class', 7), 'passed'),
        ReportItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'TestObject2::teardown_class', 7), 'passed'),
        ReportItem('test', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::test1', 11), 'passed'),
        ReportItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject1::test1', 11), 'passed'),
        ReportItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject2::test1', 11), 'passed'),
        ReportItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject2::test2', 6), 'passed'),
    ]


def test_class_setup(testdir):
    test_file = 'fixtures/test_class_setup.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert scheduler.suite_items == [
        SuiteItem('setup', Location(test_file, 'TestObject::setup_class', 6), 42, []),
        SuiteItem('test', Location(test_file, 'TestObject::test1', 11), 42, []),
        SuiteItem('test', Location(test_file, 'TestObject::test2', 15), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'TestObject::setup_class', 6), 'passed'),
        ReportItem('test', Location(test_file, 'TestObject::test1', 11), 'passed'),
        ReportItem('test', Location(test_file, 'TestObject::test2', 15), 'passed'),
    ]


def test_class_nested(testdir):
    test_file = 'fixtures/test_class_nested.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert scheduler.suite_items == [
        SuiteItem('setup', Location(test_file, 'TestOuter::setup_class', 22), 42, []),
        SuiteItem('setup', Location(test_file, 'TestOuter::setup_method', 30), 42, []),
        SuiteItem('setup', Location(test_file, 'TestOuter::TestInner::setup_class', 5), 42, []),
        SuiteItem('setup', Location(test_file, 'TestOuter::TestInner::setup_method', 13), 42, []),
        SuiteItem('teardown', Location(test_file, 'TestOuter::teardown_class', 26), 42, []),
        SuiteItem('teardown', Location(test_file, 'TestOuter::teardown_method', 33), 42, []),
        SuiteItem('teardown', Location(test_file, 'TestOuter::TestInner::teardown_class', 9), 42, []),
        SuiteItem('teardown', Location(test_file, 'TestOuter::TestInner::teardown_method', 16), 42, []),
        SuiteItem('test', Location(test_file, 'TestOuter::test', 36), 42, []),
        SuiteItem('test', Location(test_file, 'TestOuter::TestInner::test', 19), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'TestOuter::setup_class', 22), 'passed'),  # this is what changes
        ReportItem('setup', Location(test_file, 'TestOuter::setup_method', 30), 'passed'),
        ReportItem('setup', Location(test_file, 'TestOuter::TestInner::setup_class', 5), 'passed'),
        ReportItem('setup', Location(test_file, 'TestOuter::TestInner::setup_method', 13), 'passed'),
        ReportItem('teardown', Location(test_file, 'TestOuter::teardown_class', 26), 'passed'),
        ReportItem('teardown', Location(test_file, 'TestOuter::teardown_method', 33), 'passed'),
        ReportItem('teardown', Location(test_file, 'TestOuter::TestInner::teardown_class', 9), 'passed'),
        ReportItem('teardown', Location(test_file, 'TestOuter::TestInner::teardown_method', 16), 'passed'),
        ReportItem('test', Location(test_file, 'TestOuter::test', 36), 'passed'),
        ReportItem('test', Location(test_file, 'TestOuter::TestInner::test', 19), 'passed'),
    ]


def test_class_setup_fail(testdir):
    test_file = 'fixtures/test_class_setup_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'TestObject::setup_class', 3), 'failed',
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, 'TestObject::test', 7), 'failed'),
    ]


def test_class_method_setup_fail(testdir):
    test_file = 'fixtures/test_class_method_setup_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.suite_items == [
        SuiteItem('setup', Location(test_file, 'TestObject::setup_method', 3), 42, []),
        SuiteItem('test', Location(test_file, 'TestObject::test', 6), 42, []),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, 'TestObject::setup_method', 3), 'failed',
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, 'TestObject::test', 6), 'failed'),
    ]


def test_class_teardown(testdir):
    test_file = 'fixtures/test_class_teardown.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, 'TestObject::teardown_class', 3), 'passed'),
        ReportItem('test', Location(test_file, 'TestObject::test', 7), 'passed'),
    ]


def test_class_teardown_fail(testdir):
    test_file = 'fixtures/test_class_teardown_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, 'TestObject::teardown_class', 3), 'failed',
                   Failure('Exception', 'teardown failed')),
        ReportItem('test', Location(test_file, 'TestObject::test', 7), 'passed'),
    ]


def test_class_method_teardown_fail(testdir):
    test_file = 'fixtures/test_class_method_teardown_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, 'TestObject::teardown_method', 3), 'failed',
                   Failure('Exception', 'teardown failed')),
        ReportItem('test', Location(test_file, 'TestObject::test', 6), 'passed'),
    ]


def test_package(testdir):
    init_file = 'fixtures/package/__init__.py'
    test_file = 'fixtures/package/test_pass.py'
    (result, scheduler) = run_test(testdir, [init_file, test_file])
    assert_outcomes(result, passed=1)


def test_load_failed(testdir):
    test_file = 'fixtures/load_failed.py'
    (_, scheduler) = run_test(testdir, [test_file])

    assert scheduler.suite_items == []
    assert scheduler.report_items == []


def test_settings(testdir):
    run_test(testdir, ['fixtures/test_class.py'])

    settings = maketestsgofaster.plugin.settings

    assert settings.runner_name == 'pytest'
    assert settings.runner_plugins == {('pytest-cov', '2.5.1'), ('pytest-mock', '1.6.3'), ('maketestsgofaster', '1.0.0')}
    assert settings.runner_root == os.getcwd()
    assert settings.runner_version == pytest.__version__


# ================================ HELPERS ================================


@pytest.fixture(scope='module', autouse=True)
def mock_schedule():
    previous = maketestsgofaster.scheduler.Scheduler
    maketestsgofaster.scheduler.Scheduler = MockScheduler
    yield
    maketestsgofaster.scheduler.Scheduler = previous


def run_test(pyt, files, *args):
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
    return (test_result, maketestsgofaster.plugin.scheduler)


def assert_outcomes(result, passed=0, skipped=0, failed=0, error=0):
    d = result.parseoutcomes()
    obtained = {
        'passed': d.get('passed', 0),
        'skipped': d.get('skipped', 0),
        'failed': d.get('failed', 0),
        'error': d.get('error', 0),
    }
    assert obtained == dict(passed=passed, skipped=skipped, failed=failed, error=error)

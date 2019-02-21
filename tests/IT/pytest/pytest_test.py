import os
import os.path
from pytest import __version__

from tests.IT.util import MockScheduler, round_file_size, round_time

from maketestsgofaster.model import Failure, Location, ReportItem, SuiteItem
import maketestsgofaster.pytest


def test_function_pass(testdir):
    test_file = 'fixtures/test_function_pass.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test_pass', 1), 'passed', 0.1, None),
    ]


def test_function_fail(testdir):
    test_file = 'fixtures/test_function_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, failed=1)

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test_fail', 1), 'failed', 0.1,
                   Failure('AssertionError', 'assert (2 + 2) == 22')),
    ]


def test_function_skip(testdir):
    test_file = 'fixtures/test_function_skip.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, skipped=1)

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test_skip', 4), 'skipped', 0.1, None),
    ]


def test_function_xfail(testdir):
    test_file = 'fixtures/test_function_xfail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=0)

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test_xfail', 4), 'skipped', 0.1,
                   Failure('AssertionError', 'assert (1 + 2) == 12')),
    ]


def test_function_setup(testdir):
    test_file = 'fixtures/test_function_setup.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test', 5), 42, []),
    ]

    assert report_items() == [
        ReportItem('setup', Location(test_file, 'setup_function', 1), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test', 5), 'passed', 0.1, None),
    ]


def test_function_setup_fail(testdir):
    test_file = 'fixtures/test_function_setup_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert report_items() == [
        ReportItem('setup', Location(test_file, 'setup_function', 1), 'failed', 0.1,
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, 'test', 5), 'failed', 0.1, None),
    ]


def test_function_teardown(testdir):
    test_file = 'fixtures/test_function_teardown.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test', 5), 42, []),
    ]

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test', 5), 'passed', 0.1, None),
        ReportItem('teardown', Location(test_file, 'teardown_function', 1), 'passed', 0.1, None),
    ]


def test_function_teardown_fail(testdir):
    test_file = 'fixtures/test_function_teardown_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test', 5), 'passed', 0.1, None),
        ReportItem('teardown', Location(test_file, 'teardown_function', 1), 'failed', 0.1,
                   Failure('Exception', 'teardown failed')),
    ]


def test_function_parameterized(testdir):
    test_file = 'fixtures/test_function_param.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=3)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test_param[3+5-8]', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test_param[2+4-6]', 4), 42, []),
        SuiteItem('test', Location(test_file, 'test_param[6*9-54]', 4), 42, []),
    ]

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test_param[3+5-8]', 4), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test_param[2+4-6]', 4), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test_param[6*9-54]', 4), 'passed', 0.1, None),
    ]


def test_module_setup(testdir):
    test_file = 'fixtures/test_module_setup.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test1', 9), 42, []),
        SuiteItem('test', Location(test_file, 'test2', 14), 42, []),
    ]

    assert report_items() == [
        ReportItem('setup', Location(test_file, 'setup_module', 4), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test1', 9), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test2', 14), 'passed', 0.1, None),
    ]


def test_module_setup_fail(testdir):
    test_file = 'fixtures/test_module_setup_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert report_items() == [
        ReportItem('setup', Location(test_file, 'setup_module', 1), 'failed', 0.1,
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, 'test', 5), 'failed', 0.1, None),
    ]


def test_module_teardown(testdir):
    test_file = 'fixtures/test_module_teardown.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test', 9), 42, []),
    ]

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test', 9), 'passed', 0.1, None),
        ReportItem('teardown', Location(test_file, 'teardown_module', 4), 'passed', 0.1, None),
    ]


def test_module_teardown_fail(testdir):
    test_file = 'fixtures/test_module_teardown_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test', 5), 'passed', 0.1, None),
        ReportItem('teardown', Location(test_file, 'teardown_module', 1), 'failed', 0.1,
                   Failure('Exception', 'teardown failed')),
    ]


def test_fixture(testdir):
    test_file = 'fixtures/test_fixture.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test_with_fixture', 9), 42, [
            SuiteItem('fixture', Location(test_file, 'fixture', 4), 42, []),
        ]),
    ]

    assert report_items() == [
        ReportItem('fixture', Location(test_file, 'fixture', 4), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test_with_fixture', 9), 'passed', 0.1, None),
    ]


def test_fixtures(testdir):
    test_file = 'fixtures/test_fixtures.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test_with_fixtures', 14), 42, [
            SuiteItem('fixture', Location(test_file, 'fixture1', 4), 42, []),
            SuiteItem('fixture', Location(test_file, 'fixture2', 9), 42, []),
        ]),
    ]

    assert report_items() == [
        ReportItem('fixture', Location(test_file, 'fixture1', 4), 'passed', 0.1, None),
        ReportItem('fixture', Location(test_file, 'fixture2', 9), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test_with_fixtures', 14), 'passed', 0.1, None),
    ]


def test_fixture_nested(testdir):
    test_file = 'fixtures/test_fixture_nested.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test_with_fixture', 14), 42, [
            SuiteItem('fixture', Location(test_file, 'fixture1', 4), 42, []),
            SuiteItem('fixture', Location(test_file, 'fixture2', 9), 42, []),
        ]),
    ]

    # note that nested fixtures are evaluated sequentially, one _after_ the other
    assert report_items() == [
        ReportItem('fixture', Location(test_file, 'fixture1', 4), 'passed', 0.1, None),
        ReportItem('fixture', Location(test_file, 'fixture2', 9), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test_with_fixture', 14), 'passed', 0.1, None),
    ]


def test_fixture_session(testdir):
    test_file = 'fixtures/test_fixture_session.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test_with_fixture', 1), 42, [
            SuiteItem('fixture', Location('fixtures/conftest.py', 'fixture_session', 4), 42, []),
        ]),
    ]

    assert report_items() == [
        ReportItem('fixture', Location('fixtures/conftest.py', 'fixture_session', 4), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test_with_fixture', 1), 'passed', 0.1, None),
    ]


def test_fixture_missing(testdir):
    test_file = 'fixtures/test_fixture_missing.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test_with_missing_fixture', 1), 42, []),
    ]

    assert report_items() == [
        ReportItem('test', Location(test_file, 'test_with_missing_fixture', 1), 'failed', 0.1, None),
    ]


def test_fixture_import(testdir):
    test_file = 'fixtures/test_fixture_import.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test_with_fixture', 5), 42, [
            SuiteItem('fixture', Location('fixtures/fixture.py', 'fixture_import', 4), 42, []),
        ]),
    ]

    assert report_items() == [
        ReportItem('fixture', Location('fixtures/fixture.py', 'fixture_import', 4), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'test_with_fixture', 5), 'passed', 0.1, None),
    ]


def test_fixture_fail(testdir):
    test_file = 'fixtures/test_fixture_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'test_with_fixture', 9), 42, [
            SuiteItem('fixture', Location(test_file, 'fixture', 4), 42, []),
        ]),
    ]

    assert report_items() == [
        ReportItem('fixture', Location(test_file, 'fixture', 4), 'error', 0.1,
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, 'test_with_fixture', 9), 'failed', 0.1, None),
    ]


def test_multiple_test_files(testdir):
    result = run_test(testdir, ['fixtures/test_function_fail.py', 'fixtures/test_function_pass.py', 'fixtures/test_function_skip.py'])
    assert_outcomes(result, failed=1, passed=1, skipped=1)

    items = report_items()
    assert len(items) == 3


def test_class(testdir):
    test_file = 'fixtures/test_class.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'TestObject::test', 3), 42, []),
    ]

    assert report_items() == [
        ReportItem('test', Location(test_file, 'TestObject::test', 3), 'passed', 0.1, None),
    ]


def test_class_inheritance(testdir):
    result = run_test(testdir, ['fixtures/test_class_inheritance_1.py', 'fixtures/test_class_inheritance_2.py'])
    assert_outcomes(result, passed=4)

    assert suite_items() == [
        SuiteItem('test', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::test1', 11), 42, []),
        SuiteItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject1::test1', 11), 42, []),
        SuiteItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject2::test1', 11), 42, []),
        SuiteItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject2::test2', 6), 42, []),
    ]

    assert report_items() == [
        ReportItem('setup', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::setup_class', 3), 'passed', 0.1, None),
        ReportItem('test', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::test1', 11), 'passed', 0.1, None),
        ReportItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::teardown_class', 7), 'passed', 0.1, None),

        ReportItem('setup', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::setup_class', 3), 'passed', 0.1, None),
        ReportItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject1::test1', 11), 'passed', 0.1, None),
        ReportItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'TestObject1::teardown_class', 7), 'passed', 0.1, None),

        ReportItem('setup', Location('fixtures/test_class_inheritance_1.py', 'TestObject2::setup_class', 3), 'passed', 0.1, None),
        ReportItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject2::test1', 11), 'passed', 0.1, None),
        ReportItem('test', Location('fixtures/test_class_inheritance_2.py', 'TestObject2::test2', 6), 'passed', 0.1, None),
        ReportItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'TestObject2::teardown_class', 7), 'passed', 0.1, None),
    ]


def test_class_setup(testdir):
    test_file = 'fixtures/test_class_setup.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'TestObject::test1', 11), 42, []),
        SuiteItem('test', Location(test_file, 'TestObject::test2', 15), 42, []),
    ]

    assert report_items() == [
        ReportItem('setup', Location(test_file, 'TestObject::setup_class', 6), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'TestObject::test1', 11), 'passed', 0.1, None),
        ReportItem('test', Location(test_file, 'TestObject::test2', 15), 'passed', 0.1, None),
    ]


def test_class_nested(testdir):
    test_file = 'fixtures/test_class_nested.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'TestOuter::TestInner::test', 19), 42, []),
        SuiteItem('test', Location(test_file, 'TestOuter::test', 36), 42, []),
    ]

    if __version__.split('.')[0] == '3':
        assert report_items() == [
            ReportItem('setup', Location(test_file, 'TestOuter::setup_class', 22), 'passed', 0.1, None),  # this is what changes
            ReportItem('setup', Location(test_file, 'TestOuter::TestInner::setup_class', 5), 'passed', 0.1, None),
            ReportItem('setup', Location(test_file, 'TestOuter::TestInner::setup_method', 13), 'passed', 0.1, None),
            ReportItem('test', Location(test_file, 'TestOuter::TestInner::test', 19), 'passed', 0.1, None),
            ReportItem('teardown', Location(test_file, 'TestOuter::TestInner::teardown_method', 16), 'passed', 0.1, None),
            ReportItem('teardown', Location(test_file, 'TestOuter::TestInner::teardown_class', 9), 'passed', 0.1, None),
            ReportItem('setup', Location(test_file, 'TestOuter::setup_method', 30), 'passed', 0.1, None),
            ReportItem('test', Location(test_file, 'TestOuter::test', 36), 'passed', 0.1, None),
            ReportItem('teardown', Location(test_file, 'TestOuter::teardown_method', 33), 'passed', 0.1, None),
            ReportItem('teardown', Location(test_file, 'TestOuter::teardown_class', 26), 'passed', 0.1, None),
        ]
    else:
        assert report_items() == [
            ReportItem('setup', Location(test_file, 'TestOuter::TestInner::setup_class', 5), 'passed', 0.1, None),
            ReportItem('setup', Location(test_file, 'TestOuter::TestInner::setup_method', 13), 'passed', 0.1, None),
            ReportItem('test', Location(test_file, 'TestOuter::TestInner::test', 19), 'passed', 0.1, None),
            ReportItem('teardown', Location(test_file, 'TestOuter::TestInner::teardown_method', 16), 'passed', 0.1, None),
            ReportItem('teardown', Location(test_file, 'TestOuter::TestInner::teardown_class', 9), 'passed', 0.1, None),
            ReportItem('setup', Location(test_file, 'TestOuter::setup_class', 22), 'passed', 0.1, None),  # this is what changes
            ReportItem('setup', Location(test_file, 'TestOuter::setup_method', 30), 'passed', 0.1, None),
            ReportItem('test', Location(test_file, 'TestOuter::test', 36), 'passed', 0.1, None),
            ReportItem('teardown', Location(test_file, 'TestOuter::teardown_method', 33), 'passed', 0.1, None),
            ReportItem('teardown', Location(test_file, 'TestOuter::teardown_class', 26), 'passed', 0.1, None),
        ]


def test_class_setup_fail(testdir):
    test_file = 'fixtures/test_class_setup_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert report_items() == [
        ReportItem('setup', Location(test_file, 'TestObject::setup_class', 3), 'failed', 0.1,
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, 'TestObject::test', 7), 'failed', 0.1, None),
    ]


def test_class_method_setup_fail(testdir):
    test_file = 'fixtures/test_class_method_setup_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert suite_items() == [
        SuiteItem('test', Location(test_file, 'TestObject::test', 6), 42, []),
    ]

    assert report_items() == [
        ReportItem('setup', Location(test_file, 'TestObject::setup_method', 3), 'failed', 0.1,
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, 'TestObject::test', 6), 'failed', 0.1, None),
    ]


def test_class_teardown(testdir):
    test_file = 'fixtures/test_class_teardown.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert report_items() == [
        ReportItem('test', Location(test_file, 'TestObject::test', 7), 'passed', 0.1, None),
        ReportItem('teardown', Location(test_file, 'TestObject::teardown_class', 3), 'passed', 0.1, None),
    ]


def test_class_teardown_fail(testdir):
    test_file = 'fixtures/test_class_teardown_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert report_items() == [
        ReportItem('test', Location(test_file, 'TestObject::test', 7), 'passed', 0.1, None),
        ReportItem('teardown', Location(test_file, 'TestObject::teardown_class', 3), 'failed', 0.1,
                   Failure('Exception', 'teardown failed')),
    ]


def test_class_method_teardown_fail(testdir):
    test_file = 'fixtures/test_class_method_teardown_fail.py'
    result = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert report_items() == [
        ReportItem('test', Location(test_file, 'TestObject::test', 6), 'passed', 0.1, None),
        ReportItem('teardown', Location(test_file, 'TestObject::teardown_method', 3), 'failed', 0.1,
                   Failure('Exception', 'teardown failed')),
    ]


def test_package(testdir):
    init_file = 'fixtures/package/__init__.py'
    test_file = 'fixtures/package/test_pass.py'
    result = run_test(testdir, [init_file, test_file])
    assert_outcomes(result, passed=1)


def test_load_failed(testdir):
    test_file = 'fixtures/load_failed.py'
    run_test(testdir, [test_file])

    assert suite_items() == []
    assert report_items() == []


def test_settings(testdir):
    run_test(testdir, ['fixtures/test_class.py'])

    settings = plugin_settings()

    assert settings.runner_name == 'pytest'
    assert settings.runner_plugins == {('pytest-cov', '2.5.1'), ('pytest-mock', '1.6.3'), ('maketestsgofaster', '1.0.0')}
    assert settings.runner_root == os.getcwd()
    assert settings.runner_version == __version__


# ================================ HELPERS ================================


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
    return pyt.runpytest()


def assert_outcomes(result, passed=0, skipped=0, failed=0, error=0):
    d = result.parseoutcomes()
    obtained = {
        'passed': d.get('passed', 0),
        'skipped': d.get('skipped', 0),
        'failed': d.get('failed', 0),
        'error': d.get('error', 0),
    }
    assert obtained == dict(passed=passed, skipped=skipped, failed=failed, error=error)


def suite_items():
    return round_file_size(maketestsgofaster.pytest.scheduler.suite_builder.items)


def report_items():
    return round_time(maketestsgofaster.pytest.scheduler.report_builder.items)


def plugin_settings():
    return maketestsgofaster.pytest.settings


maketestsgofaster.pytest.create_scheduler = \
    lambda settings: MockScheduler(settings)

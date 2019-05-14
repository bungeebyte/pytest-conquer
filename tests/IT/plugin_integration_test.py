import os
import os.path
import sys

import pytest

import testandconquer.scheduler
from testandconquer.model import Failure, Location, ReportItem, SuiteItem, Tag

from tests.mock.settings import MockSettings
from tests.mock.scheduler import MockScheduler


def test_function_pass(testdir):
    test_file = 'fixtures/test_function_pass.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_pass', 1)),
    ]

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_pass', 1), 'passed'),
    ]


def test_function_fail(testdir):
    test_file = 'fixtures/test_function_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, failed=1)

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_fail', 1), 'failed',
                   Failure('AssertionError', 'assert (2 + 2) == 22')),
    ]


def test_function_skip(testdir):
    test_file = 'fixtures/test_function_skip.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, skipped=1)

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_skip', 4), 'skipped'),
    ]


def test_function_xfail(testdir):
    test_file = 'fixtures/test_function_xfail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=0)

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_xfail', 4), 'skipped',
                   Failure('AssertionError', 'assert (1 + 2) == 12')),
    ]


@pytest.mark.wip
def test_function_setup(testdir):
    test_file = 'fixtures/test_function_setup.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('setup', Location(test_file, module_for(test_file), None, 'setup_function', 1), scope='function'),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test', 5)),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'setup_function', 1), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test', 5), 'passed'),
    ]


def test_function_setup_fail(testdir):
    test_file = 'fixtures/test_function_setup_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'setup_function', 1), 'failed',
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test', 5), 'failed'),
    ]


def test_function_teardown(testdir):
    test_file = 'fixtures/test_function_teardown.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('teardown', Location(test_file, module_for(test_file), None, 'teardown_function', 1), scope='function'),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test', 5)),
    ]

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'teardown_function', 1), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test', 5), 'passed'),
    ]


def test_function_teardown_fail(testdir):
    test_file = 'fixtures/test_function_teardown_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'teardown_function', 1), 'failed',
                   Failure('Exception', 'teardown failed')),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test', 5), 'passed'),
    ]


def test_function_parameterized(testdir):
    test_file = 'fixtures/test_function_param.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=3)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_param[2+4-6]', 4)),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_param[3+5-8]', 4)),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_param[6*9-54]', 4)),
    ]

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_param[2+4-6]', 4), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_param[3+5-8]', 4), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_param[6*9-54]', 4), 'passed'),
    ]


def test_function_tag(testdir):
    test_file = 'fixtures/test_function_tag.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_pass', 4), tags=[Tag('test', False)]),
    ]

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_pass', 4), 'passed'),
    ]


def test_module_setup(testdir):
    test_file = 'fixtures/test_module_setup.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('setup', Location(test_file, module_for(test_file), None, 'setup_module', 4), scope='module'),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test1', 9)),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test2', 14)),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'setup_module', 4), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test1', 9), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test2', 14), 'passed'),
    ]


def test_module_setup_fail(testdir):
    test_file = 'fixtures/test_module_setup_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'setup_module', 1), 'failed',
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test', 5), 'failed'),
    ]


def test_module_teardown(testdir):
    test_file = 'fixtures/test_module_teardown.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('teardown', Location(test_file, module_for(test_file), None, 'teardown_module', 4), scope='module'),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test', 9)),
    ]

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'teardown_module', 4), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test', 9), 'passed'),
    ]


def test_module_teardown_fail(testdir):
    test_file = 'fixtures/test_module_teardown_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'teardown_module', 1), 'failed',
                   Failure('Exception', 'teardown failed')),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test', 5), 'passed'),
    ]


def test_fixture(testdir):
    test_file = 'fixtures/test_fixture.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture', 4)),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 9), deps=[
            SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture', 4)),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'fixture', 4), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'fixture', 4), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 9), 'passed'),
    ]


def test_fixtures(testdir):
    test_file = 'fixtures/test_fixtures.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture1', 4)),
        SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture2', 9)),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixtures', 14), deps=[
            SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture1', 4)),
            SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture2', 9)),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'fixture1', 4), 'passed'),
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'fixture2', 9), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'fixture1', 4), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'fixture2', 9), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixtures', 14), 'passed'),
    ]


def test_fixture_nested(testdir):
    test_file = 'fixtures/test_fixture_nested.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture1', 4)),
        SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture2', 9)),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 14), deps=[
            SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture1', 4)),
            SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture2', 9)),
        ]),
    ]

    # note that nested fixtures are evaluated sequentially, one _after_ the other
    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'fixture1', 4), 'passed'),
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'fixture2', 9), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'fixture1', 4), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'fixture2', 9), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'fixture2', 9), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 14), 'passed'),
    ]


def test_fixture_session(testdir):
    test_file = 'fixtures/test_fixture_session.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location('fixtures/conftest.py'), size=42),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('fixture', Location('fixtures/conftest.py', 'conftest', None, 'fixture_session', 4)),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 1), deps=[
            SuiteItem('fixture', Location('fixtures/conftest.py', 'conftest', None, 'fixture_session', 4)),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location('fixtures/conftest.py', 'conftest', None, 'fixture_session', 4), 'passed'),
        ReportItem('teardown', Location('fixtures/conftest.py', 'conftest', None, 'fixture_session', 4), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 1), 'passed'),
    ]


def test_fixture_missing(testdir):
    test_file = 'fixtures/test_fixture_missing.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_with_missing_fixture', 1)),
    ]

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_with_missing_fixture', 1), 'failed'),
    ]


def test_fixture_import(testdir):
    test_file = 'fixtures/test_fixture_import.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location('fixtures/fixture.py'), size=42),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('fixture', Location('fixtures/fixture.py', 'fixture', None, 'fixture_import', 4)),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 5), deps=[
            SuiteItem('fixture', Location('fixtures/fixture.py', 'fixture', None, 'fixture_import', 4)),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location('fixtures/fixture.py', 'fixture', None, 'fixture_import', 4), 'passed'),
        ReportItem('teardown', Location('fixtures/fixture.py', 'fixture', None, 'fixture_import', 4), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 5), 'passed'),
    ]


def test_fixture_fail(testdir):
    test_file = 'fixtures/test_fixture_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture', 4)),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 9), deps=[
            SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture', 4)),
        ]),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), None, 'fixture', 4), 'error',
                   Failure('Exception', 'setup failed')),
        ReportItem('teardown', Location(test_file, module_for(test_file), None, 'fixture', 4), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 9), 'failed'),
    ]


def test_fixture_tag(testdir):
    test_file = 'fixtures/test_fixture_tag.py'
    (_, scheduler) = run_test(testdir, [test_file])

    assert scheduler.suite_items == [
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture', 4), tags=[Tag('my_group', True)]),
        SuiteItem('test', Location(test_file, module_for(test_file), None, 'test_with_fixture', 10), deps=[
            SuiteItem('fixture', Location(test_file, module_for(test_file), None, 'fixture', 4), tags=[Tag('my_group', True)]),
        ]),
    ]


def test_multiple_test_files(testdir):
    (result, scheduler) = run_test(testdir, ['fixtures/test_function_fail.py', 'fixtures/test_function_pass.py', 'fixtures/test_function_skip.py'])
    assert_outcomes(result, failed=1, passed=1, skipped=1)

    assert len(scheduler.report_items) == 3


def test_class(testdir):
    test_file = 'fixtures/test_class.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('class', Location(test_file, module_for(test_file), 'TestObject', None, 1)),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 3)),
    ]

    assert scheduler.report_items == [
        ReportItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 3), 'passed'),
    ]


def test_class_tags(testdir):
    test_file = 'fixtures/test_class_tag.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('class', Location(test_file, module_for(test_file), 'TestObject', None, 5), tags=[Tag('my_group', False)]),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 7)),
    ]


def test_class_inheritance(testdir):
    (result, scheduler) = run_test(testdir, ['fixtures/test_class_inheritance_1.py', 'fixtures/test_class_inheritance_2.py'])
    assert_outcomes(result, passed=3)

    assert scheduler.suite_items == [
        SuiteItem('class', Location('fixtures/test_class_inheritance_1.py', 'test_class_inheritance_1', 'TestObject1', None, 1)),
        SuiteItem('class', Location('fixtures/test_class_inheritance_2.py', 'test_class_inheritance_2', 'TestObject2', None, 4)),
        SuiteItem('file', Location('fixtures/test_class_inheritance_1.py'), size=42),
        SuiteItem('file', Location('fixtures/test_class_inheritance_2.py'), size=42),
        SuiteItem('setup', Location('fixtures/test_class_inheritance_1.py', 'test_class_inheritance_1', 'TestObject1', 'setup_class', 3), scope='class'),
        SuiteItem('setup', Location('fixtures/test_class_inheritance_2.py', 'test_class_inheritance_2', 'TestObject2', 'setup_class', 3), scope='class'),
        SuiteItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'test_class_inheritance_1', 'TestObject1', 'teardown_class', 7), scope='class'),
        SuiteItem('teardown', Location('fixtures/test_class_inheritance_2.py', 'test_class_inheritance_2', 'TestObject2', 'teardown_class', 7), scope='class'),
        SuiteItem('test', Location('fixtures/test_class_inheritance_1.py', 'test_class_inheritance_1', 'TestObject1', 'test1', 11)),
        SuiteItem('test', Location('fixtures/test_class_inheritance_2.py', 'test_class_inheritance_2', 'TestObject2', 'test1', 11)),
        SuiteItem('test', Location('fixtures/test_class_inheritance_2.py', 'test_class_inheritance_2', 'TestObject2', 'test2', 6)),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location('fixtures/test_class_inheritance_1.py', 'test_class_inheritance_1', 'TestObject1', 'setup_class', 3), 'passed'),
        ReportItem('setup', Location('fixtures/test_class_inheritance_2.py', 'test_class_inheritance_2', 'TestObject2', 'setup_class', 3), 'passed'),
        ReportItem('teardown', Location('fixtures/test_class_inheritance_1.py', 'test_class_inheritance_1', 'TestObject1', 'teardown_class', 7), 'passed'),
        ReportItem('teardown', Location('fixtures/test_class_inheritance_2.py', 'test_class_inheritance_2', 'TestObject2', 'teardown_class', 7), 'passed'),
        ReportItem('test', Location('fixtures/test_class_inheritance_1.py', 'test_class_inheritance_1', 'TestObject1', 'test1', 11), 'passed'),
        ReportItem('test', Location('fixtures/test_class_inheritance_2.py', 'test_class_inheritance_2', 'TestObject2', 'test1', 11), 'passed'),
        ReportItem('test', Location('fixtures/test_class_inheritance_2.py', 'test_class_inheritance_2', 'TestObject2', 'test2', 6), 'passed'),
    ]


def test_class_setup(testdir):
    test_file = 'fixtures/test_class_setup.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert scheduler.suite_items == [
        SuiteItem('class', Location(test_file, module_for(test_file), 'TestObject', None, 4)),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('setup', Location(test_file, module_for(test_file), 'TestObject', 'setup_class', 6), scope='class'),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test1', 11)),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test2', 15)),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), 'TestObject', 'setup_class', 6), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test1', 11), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test2', 15), 'passed'),
    ]


def test_class_setup_tag(testdir):
    test_file = 'fixtures/test_class_setup_tag.py'
    (_, scheduler) = run_test(testdir, [test_file])

    assert scheduler.suite_items == [
        SuiteItem('class', Location(test_file, module_for(test_file), 'TestObject', None, 4)),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('setup', Location(test_file, module_for(test_file), 'TestObject', 'setup_class', 6), scope='class', tags=[Tag('my_group', False)]),
    ]


def test_class_param(testdir):
    test_file = 'fixtures/test_class_param.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert scheduler.suite_items == [
        SuiteItem('class', Location(test_file, module_for(test_file), 'TestObject', None, 4)),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test_param[2+4-6]', 6)),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test_param[3+5-8]', 6)),
    ]


def test_class_decorator(testdir):
    test_file = 'fixtures/test_class_decorator.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.suite_items == [
        SuiteItem('class', Location(test_file, module_for(test_file), 'TestObject', None, 4)),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 6)),
    ]


def test_class_nested(testdir):
    test_file = 'fixtures/test_class_nested.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=2)

    assert scheduler.suite_items == [
        SuiteItem('class', Location(test_file, module_for(test_file), 'TestOuter', None, 1)),
        SuiteItem('class', Location(test_file, module_for(test_file), 'TestOuter.TestInner', None, 3)),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('setup', Location(test_file, module_for(test_file), 'TestOuter', 'setup_class', 22), scope='class'),
        SuiteItem('setup', Location(test_file, module_for(test_file), 'TestOuter', 'setup_method', 30), scope='method'),
        SuiteItem('setup', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'setup_class', 5), scope='class'),
        SuiteItem('setup', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'setup_method', 13), scope='method'),
        SuiteItem('teardown', Location(test_file, module_for(test_file), 'TestOuter', 'teardown_class', 26), scope='class'),
        SuiteItem('teardown', Location(test_file, module_for(test_file), 'TestOuter', 'teardown_method', 33), scope='method'),
        SuiteItem('teardown', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'teardown_class', 9), scope='class'),
        SuiteItem('teardown', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'teardown_method', 16), scope='method'),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestOuter', 'test', 36)),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'test', 19)),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), 'TestOuter', 'setup_class', 22), 'passed'),
        ReportItem('setup', Location(test_file, module_for(test_file), 'TestOuter', 'setup_method', 30), 'passed'),
        ReportItem('setup', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'setup_class', 5), 'passed'),
        ReportItem('setup', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'setup_method', 13), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), 'TestOuter', 'teardown_class', 26), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), 'TestOuter', 'teardown_method', 33), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'teardown_class', 9), 'passed'),
        ReportItem('teardown', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'teardown_method', 16), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), 'TestOuter', 'test', 36), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), 'TestOuter.TestInner', 'test', 19), 'passed'),
    ]


def test_class_setup_fail(testdir):
    test_file = 'fixtures/test_class_setup_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), 'TestObject', 'setup_class', 3), 'failed',
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 7), 'failed'),
    ]


def test_class_method_setup_fail(testdir):
    test_file = 'fixtures/test_class_method_setup_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1)

    assert scheduler.suite_items == [
        SuiteItem('class', Location(test_file, module_for(test_file), 'TestObject', None, 1)),
        SuiteItem('file', Location(test_file), size=42),
        SuiteItem('setup', Location(test_file, module_for(test_file), 'TestObject', 'setup_method', 3), scope='method'),
        SuiteItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 6)),
    ]

    assert scheduler.report_items == [
        ReportItem('setup', Location(test_file, module_for(test_file), 'TestObject', 'setup_method', 3), 'failed',
                   Failure('Exception', 'setup failed')),
        ReportItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 6), 'failed'),
    ]


def test_class_teardown(testdir):
    test_file = 'fixtures/test_class_teardown.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, module_for(test_file), 'TestObject', 'teardown_class', 3), 'passed'),
        ReportItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 7), 'passed'),
    ]


def test_class_teardown_fail(testdir):
    test_file = 'fixtures/test_class_teardown_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, module_for(test_file), 'TestObject', 'teardown_class', 3), 'failed',
                   Failure('Exception', 'teardown failed')),
        ReportItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 7), 'passed'),
    ]


def test_class_method_teardown_fail(testdir):
    test_file = 'fixtures/test_class_method_teardown_fail.py'
    (result, scheduler) = run_test(testdir, [test_file])
    assert_outcomes(result, error=1, passed=1)

    assert scheduler.report_items == [
        ReportItem('teardown', Location(test_file, module_for(test_file), 'TestObject', 'teardown_method', 3), 'failed',
                   Failure('Exception', 'teardown failed')),
        ReportItem('test', Location(test_file, module_for(test_file), 'TestObject', 'test', 6), 'passed'),
    ]


def test_package(testdir):
    init_file = 'fixtures/package/__init__.py'
    test_file = 'fixtures/package/test_pass.py'
    (result, scheduler) = run_test(testdir, [init_file, test_file])
    assert_outcomes(result, passed=1)


def test_collect_only_mode(testdir):
    test_file = 'fixtures/test_class.py'
    (result, scheduler) = run_test(testdir, [test_file], ['--conquer', '--collect-only'])
    assert_outcomes(result)

    assert len(testandconquer.plugin.suite_items) == 3
    assert scheduler is None


def test_disabled_plugin(testdir):
    test_file = 'fixtures/test_class.py'
    (result, scheduler) = run_test(testdir, [test_file], [])
    assert_outcomes(result, passed=1)

    assert testandconquer.plugin.suite_items == []
    assert scheduler is None


def test_settings(testdir):
    run_test(testdir, ['fixtures/test_class.py'])

    settings = testandconquer.plugin.scheduler.settings

    assert settings.client_workers == 1
    assert settings.runner_name == 'pytest'
    assert settings.runner_plugins == [('pytest-mock', '1.6.3'), ('pytest-cov', '2.5.1'), ('pytest-conquer', '1.0.0')]
    assert settings.runner_root == os.getcwd()
    assert settings.runner_version == pytest.__version__


# ================================ HELPERS ================================


def module_for(file):
    return file.replace('fixtures/', '').replace('.py', '')


@pytest.fixture(scope='module', autouse=True)
def mock_schedule():
    previous = testandconquer.scheduler.Scheduler
    testandconquer.scheduler.Scheduler = MockScheduler
    yield
    testandconquer.scheduler.Scheduler = previous


@pytest.fixture(scope='module', autouse=True)
def mock_settings():
    previous = testandconquer.settings.Settings
    testandconquer.settings.Settings = MockSettings
    yield
    testandconquer.settings.Settings = previous


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
    return (test_result, testandconquer.plugin.scheduler)


def assert_outcomes(result, passed=0, skipped=0, failed=0, error=0):
    d = result.parseoutcomes()
    obtained = {
        'passed': d.get('passed', 0),
        'skipped': d.get('skipped', 0),
        'failed': d.get('failed', 0),
        'error': d.get('error', 0),
    }
    assert obtained == dict(passed=passed, skipped=skipped, failed=failed, error=error)

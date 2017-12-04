import os
import unittest

from nose import __version__
from nose.plugins import PluginTester
from nose.plugins.capture import Capture

import maketestsgofaster.nose
from maketestsgofaster.model import Failure, Location, ReportItem, SuiteItem

from tests.IT.util import MockScheduler, round_time, round_file_size


class TestCase(PluginTester, unittest.TestCase):
    activate = '--with-maketestsgofaster'
    args = ['-v', '-s']
    plugins = [maketestsgofaster.nose.MTGFNosePlugin(), Capture()]

    @staticmethod
    def suite_path(name):
        here = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(here, 'fixtures', name)

    def assert_outcome(self, passed=0, failures=0, errors=0):
        log = str(self.output)
        if passed > 0:
            assert 'errors=' not in log, log
            assert 'failures=' not in log, log
        if failures > 0:
            assert 'failures=' + str(failures) in log, log
        if errors > 0:
            assert 'errors=' + str(errors) in log, log

        total = passed + failures + errors
        if total == 1:
            assert 'Ran ' + str(total) + ' test' in log, log
        else:
            assert 'Ran ' + str(total) + ' tests' in log, log


class TestPassing(TestCase):
    suitepath = TestCase.suite_path('function_pass')

    def test(self):
        self.assert_outcome(passed=2)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/function_pass/test.py', 'test::test_pass1', 1), 42, []),
            SuiteItem('test', Location('tests/IT/nose/fixtures/function_pass/test.py', 'test::test_pass2', 5), 42, []),
        ]

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/function_pass/test.py', 'test::test_pass1', 1), 'passed', 0.1, None),
            ReportItem('test', Location('tests/IT/nose/fixtures/function_pass/test.py', 'test::test_pass2', 5), 'passed', 0.1, None),
        ]


class TestFailing(TestCase):
    suitepath = TestCase.suite_path('function_fail')

    def test(self):
        self.assert_outcome(failures=1)

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/function_fail/test.py', 'test::test_fail', 1), 'failed', 0.1,
                       Failure('AssertionError', '')),
        ]


class TestSkipping(TestCase):
    suitepath = TestCase.suite_path('function_skip')

    def test(self):
        self.assert_outcome(passed=1)

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/function_skip/test.py', 'test::test_skip', 4), 'skipped', 0.1, None),
        ]


class TestErroring(TestCase):
    suitepath = TestCase.suite_path('function_error')

    def test(self):
        self.assert_outcome(errors=2)

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/function_error/test.py', 'test::test_error1', 1), 'error', 0.1,
                       Failure('ZeroDivisionError', 'division by zero')),
            ReportItem('test', Location('tests/IT/nose/fixtures/function_error/test.py', 'test::test_error2', 5), 'error', 0.1,
                       Failure('ValueError', 'an error')),
        ]


class TestSetup(TestCase):
    suitepath = TestCase.suite_path('function_setup')

    def test(self):
        self.assert_outcome(passed=1)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/function_setup/test.py', 'test::test', 11), 42, [
                SuiteItem('setup', Location('tests/IT/nose/fixtures/function_setup/test.py', 'test::setup_function', 6), 42, []),
            ]),
        ]

        assert report_items() == [
            ReportItem('setup', Location('tests/IT/nose/fixtures/function_setup/test.py', 'test::setup_function', 6), 'passed', 0.1, None),
            ReportItem('test', Location('tests/IT/nose/fixtures/function_setup/test.py', 'test::test', 11), 'passed', 0.1, None),
        ]


class TestSetupFail(TestCase):
    suitepath = TestCase.suite_path('function_setup_fail')

    def test(self):
        self.assert_outcome(errors=1)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/function_setup_fail/test.py', 'test::test', 8), 42, [
                SuiteItem('setup', Location('tests/IT/nose/fixtures/function_setup_fail/test.py', 'test::setup_function', 4), 42, []),
            ]),
        ]

        assert report_items() == [
            ReportItem('setup', Location('tests/IT/nose/fixtures/function_setup_fail/test.py', 'test::setup_function', 4), 'error', 0.1,
                       Failure('RuntimeError', 'setup failed')),
            ReportItem('test', Location('tests/IT/nose/fixtures/function_setup_fail/test.py', 'test::test', 8), 'error', 0.0, None),
        ]


class TestTeardown(TestCase):
    suitepath = TestCase.suite_path('function_teardown')

    def test(self):
        self.assert_outcome(passed=1)

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/function_teardown/test.py', 'test::test', 8), 'passed', 0.1, None),
            ReportItem('teardown', Location('tests/IT/nose/fixtures/function_teardown/test.py', 'test::teardown_function', 4), 'passed', 0.1, None),
        ]


class TestTeardownFail(TestCase):
    suitepath = TestCase.suite_path('function_teardown_fail')

    def test(self):
        self.assert_outcome(errors=1)

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/function_teardown_fail/test.py', 'test::test', 8), 'error', 0.1, None),
            ReportItem('teardown', Location('tests/IT/nose/fixtures/function_teardown_fail/test.py', 'test::teardown_function', 4), 'error', 0.1,
                       Failure('RuntimeError', 'teardown failed')),
        ]


class TestModuleSetup(TestCase):
    suitepath = TestCase.suite_path('module_setup')

    def test(self):
        self.assert_outcome(passed=1)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/module_setup/test.py', 'test::test', 9), 42, []),
        ]

        assert report_items() == [
            ReportItem('setup', Location('tests/IT/nose/fixtures/module_setup/test.py', 'test::setup_module', 4), 'passed', 0.1, None),
            ReportItem('test', Location('tests/IT/nose/fixtures/module_setup/test.py', 'test::test', 9), 'passed', 0.1, None),
        ]


class TestModuleTeardown(TestCase):
    suitepath = TestCase.suite_path('module_teardown')

    def test(self):
        self.assert_outcome(passed=1)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/module_teardown/test.py', 'test::test', 5), 42, []),
        ]

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/module_teardown/test.py', 'test::test', 5), 'passed', 0.1, None),
            ReportItem('teardown', Location('tests/IT/nose/fixtures/module_teardown/test.py', 'test::teardown_module', 1), 'passed', 0.1, None),
        ]


class TestPackageSetup(TestCase):
    suitepath = TestCase.suite_path('package_setup')

    def test(self):
        self.assert_outcome(passed=1)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/package_setup/tests/test.py', 'tests.test::test', 1), 42, []),
        ]

        assert report_items() == [
            ReportItem('setup', Location('tests/IT/nose/fixtures/package_setup/tests/__init__.py', 'tests::setup_package', 1), 'passed', 0.1, None),
            ReportItem('test', Location('tests/IT/nose/fixtures/package_setup/tests/test.py', 'tests.test::test', 1), 'passed', 0.1, None),
        ]


class TestPackageTeardown(TestCase):
    suitepath = TestCase.suite_path('package_teardown')

    def test(self):
        self.assert_outcome(passed=1)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/package_teardown/tests/test.py', 'tests.test::test', 1), 42, []),
        ]

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/package_teardown/tests/test.py', 'tests.test::test', 1), 'passed', 0.1, None),
            ReportItem('teardown', Location('tests/IT/nose/fixtures/package_teardown/tests/__init__.py', 'tests::teardown_package', 1), 'passed', 0.1, None),
        ]


class TestLoadFailure(TestCase):
    suitepath = TestCase.suite_path('load_failure')

    def test(self):
        assert suite_items() == []
        assert report_items() == []


class TestClassPass(TestCase):
    suitepath = TestCase.suite_path('class_pass')

    def test(self):
        self.assert_outcome(passed=1)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/class_pass/test.py', 'test::TestObject.test', 3), 42, []),
        ]

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/class_pass/test.py', 'test::TestObject.test', 3), 'passed', 0.1, None),
        ]


class TestClassSetup(TestCase):
    suitepath = TestCase.suite_path('class_setup')

    def test(self):
        self.assert_outcome(passed=1)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/class_setup/test.py', 'test::TestObject.test', 11), 42, []),
        ]

        assert report_items() == [
            ReportItem('setup', Location('tests/IT/nose/fixtures/class_setup/test.py', 'test::TestObject.setup_class', 6), 'passed', 0.1, None),
            ReportItem('test', Location('tests/IT/nose/fixtures/class_setup/test.py', 'test::TestObject.test', 11), 'passed', 0.1, None),
        ]


class TestClassTeardown(TestCase):
    suitepath = TestCase.suite_path('class_teardown')

    def test(self):
        self.assert_outcome(passed=1)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/class_teardown/test.py', 'test::TestObject.test', 7), 42, []),
        ]

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/class_teardown/test.py', 'test::TestObject.test', 7), 'passed', 0.1, None),
            ReportItem('teardown', Location('tests/IT/nose/fixtures/class_teardown/test.py', 'test::TestObject.teardown_class', 3), 'passed', 0.1, None),
        ]


class TestClassSetupMethod(TestCase):
    suitepath = TestCase.suite_path('class_setup_method')

    def test(self):
        self.assert_outcome(passed=2)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/class_setup_method/test_set_up.py', 'test_set_up::TestObject.test', 6), 42, []),
            SuiteItem('test', Location('tests/IT/nose/fixtures/class_setup_method/test_setup.py', 'test_setup::TestObject.test', 6), 42, []),
        ]

        assert report_items() == [
            ReportItem('setup', Location('tests/IT/nose/fixtures/class_setup_method/test_set_up.py', 'test_set_up::TestObject.setUp', 3), 'passed', 0.1, None),
            ReportItem('test', Location('tests/IT/nose/fixtures/class_setup_method/test_set_up.py', 'test_set_up::TestObject.test', 6), 'passed', 0.1, None),
            ReportItem('setup', Location('tests/IT/nose/fixtures/class_setup_method/test_setup.py', 'test_setup::TestObject.setup', 3), 'passed', 0.1, None),
            ReportItem('test', Location('tests/IT/nose/fixtures/class_setup_method/test_setup.py', 'test_setup::TestObject.test', 6), 'passed', 0.1, None),
        ]


class TestClassTeardownMethod(TestCase):
    suitepath = TestCase.suite_path('class_teardown_method')

    def test(self):
        self.assert_outcome(passed=2)

        assert suite_items() == [
            SuiteItem('test', Location('tests/IT/nose/fixtures/class_teardown_method/test_tear_down.py', 'test_tear_down::TestObject.test', 6), 42, []),
            SuiteItem('test', Location('tests/IT/nose/fixtures/class_teardown_method/test_teardown.py', 'test_teardown::TestObject.test', 6), 42, []),
        ]

        assert report_items() == [
            ReportItem('test', Location('tests/IT/nose/fixtures/class_teardown_method/test_tear_down.py', 'test_tear_down::TestObject.test', 6), 'passed', 0.1, None),
            ReportItem('teardown', Location('tests/IT/nose/fixtures/class_teardown_method/test_tear_down.py', 'test_tear_down::TestObject.tearDown', 3), 'passed', 0.1, None),
            ReportItem('test', Location('tests/IT/nose/fixtures/class_teardown_method/test_teardown.py', 'test_teardown::TestObject.test', 6), 'passed', 0.1, None),
            ReportItem('teardown', Location('tests/IT/nose/fixtures/class_teardown_method/test_teardown.py', 'test_teardown::TestObject.teardown', 3), 'passed', 0.1, None),
        ]


class TestSettings(TestCase):
    suitepath = TestCase.suite_path('function_pass')

    def test(self):
        settings = plugin_settings()

        assert settings.runner_name == 'nose'
        assert settings.runner_plugins == {('maketestsgofaster', None), ('capture', None)}
        assert settings.runner_root == os.getcwd()
        assert settings.runner_version == __version__


# ================================ HELPERS ================================


def suite_items():
    return round_file_size(maketestsgofaster.nose.scheduler.suite_builder.items)


def report_items():
    return round_time(maketestsgofaster.nose.scheduler.report_builder.items)


def plugin_settings():
    return maketestsgofaster.nose.settings


maketestsgofaster.nose.create_scheduler = \
    lambda settings: MockScheduler(settings)

import os
import inspect
import sys
from collections import defaultdict
from time import time
from unittest import TestSuite

import nose
from nose.case import FunctionTestCase, MethodTestCase, Test
from nose.failure import Failure as PytestFailure
from nose.exc import SkipTest
from nose.plugins import Plugin
from nose.suite import ContextSuiteFactory

from maketestsgofaster import logger
from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.scheduler import Scheduler
from maketestsgofaster.cloud.settings import Capability, Settings
from maketestsgofaster.model import Failure, Location


finalizers = []
settings = None
scheduler = None
create_scheduler = lambda settings: Scheduler(settings)  # noqa: E731


class ScheduledSuite:
    def __init__(self, factory):
        self.factory = factory
        self.suites_by_location = defaultdict(list)

    def collect(self, suite, contexts=[]):
        for item in suite:
            # this happens because the loader wants to wrap the list of tests
            # in another suite - we'll just ignore that
            if item is self:
                continue
            if hasattr(item, 'test') and item.test is self:
                continue

            if isinstance(item, TestSuite):
                self.collect(item, contexts)
                continue

            if isinstance(item, Test):
                if isinstance(item.test, PytestFailure):
                    # this usually means we couldn't import the test (e.g. because of a SyntaxError)
                    continue
                test_func = item.test.test
                location = to_function_location(test_func, suite.context)
                scheduler.collect('test', location, find_setup_and_teardown(item.test))
                self.suites_by_location[location.file].append(suite)

    def __call__(self, result):
        next_file = scheduler.next_file()
        while next_file:
            suites = self.suites_by_location[next_file]
            for suite in suites:
                if not suite.has_run:  # make sure we don't run one twice
                    suite(result)
            next_file = scheduler.next_file()


class ScheduledSuiteFactory(ContextSuiteFactory):
    def __init__(self, tests=(), **kw):
        super(ScheduledSuiteFactory, self).__init__(tests, **kw)
        self.suite = ScheduledSuite(self)

    # by always returning the same scheduled suite,
    # we ensure that we can control which tests are executed
    def makeSuite(self, tests, context, **kw):  # noqa: N802
        suite = super(ScheduledSuiteFactory, self).makeSuite(tests, context, **kw)
        self.suite.collect(suite, self.context.get(suite, []))
        return self.suite


class MTGFNosePlugin(Plugin):
    name = 'maketestsgofaster'

    def configure(self, options, conf):
        global scheduler, settings
        settings = Settings(Env.create())
        settings.client_capabilities = [
            Capability.LifecycleTimings,
            Capability.SplitByFile,
        ]
        settings.runner_name = 'nose'
        for plugin in conf.plugins:
            settings.runner_plugins.add((plugin.name, None))
        settings.runner_root = conf.workingDir
        settings.runner_version = nose.__version__
        scheduler = create_scheduler(settings)
        Plugin.configure(self, options, conf)

    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env=env)

    def prepareTestLoader(self, loader):  # noqa: N802
        loader.suiteClass = ScheduledSuiteFactory(loader.config)

    def addSuccess(self, test):  # noqa: N802
        self.__report_test(test, 'passed')

    def addError(self, test, err, capt=None):  # noqa: N802
        if issubclass(err[0], SkipTest):
            status = 'skipped'
            err = None
        else:
            status = 'error'
        self.__report_test(test, status)

    def addFailure(self, test, err, capt=None, tb_info=None):  # noqa: N802
        self.__report_test(test, 'failed', err)

    def __report_test(self, test, status, err=None):
        global finalizers
        if isinstance(test, Test):
            failure = None
            time_taken = 0.0
            test_case = test.test
            location = to_function_location(test_case.test)
            if hasattr(test_case, 'started_at') and hasattr(test_case, 'ended_at'):  # if not available, test died before it ran
                time_taken = test_case.ended_at - test_case.started_at
            if status != 'skipped' and hasattr(test_case, 'exc_info'):
                failure = to_failure(test_case.exc_info)
            scheduler.report('test', location, status, time_taken, failure)
            for finalizer in finalizers:
                scheduler.report(*finalizer)
            finalizers = []
        else:
            logger.error('[nose] unable to report - not a Test: ' + str(test))


# this helps us track the _actual_ test time (excluding setup and teardown) and error
def run_test(self):
    self.exc_info = None
    self.started_at = time()
    try:
        self.test(*self.arg)
    except Exception:
        self.exc_info = sys.exc_info()
        raise
    finally:
        self.ended_at = time()


FunctionTestCase.runTest = run_test
MethodTestCase.runTest = run_test


# ======================================================================================
# SETUP / TEARDOWN REPORTING
# ======================================================================================


original_try_run_code = nose.util.try_run.__code__


def wrapped_try_run(obj, names):
    from time import time
    from maketestsgofaster.nose import finalizers, original_try_run_code, scheduler, to_failure, to_function_location

    def original_try_run(obj, names):
        pass
    original_try_run.__code__ = original_try_run_code

    start = time()

    res = None
    exc = None
    try:
        res = original_try_run(obj, names)  # actually trying to run
    except Exception:
        exc = sys.exc_info()
        raise
    finally:
        for name in names:
            func = getattr(obj, name, None)
            if func is None:
                continue

            status = 'error' if exc else 'passed'
            location = to_function_location(func)
            if [n for n in names if n.startswith('setup')]:
                scheduler.report('setup', location, status, time() - start, to_failure(exc))
            else:
                # when it's not for a test function, report right away;
                # otherwise wait until the test reporting since it happens after the teardown is run
                args = ['teardown', location, status, time() - start, to_failure(exc)]
                is_test_func_teardown = name in ('teardown', 'tearDown', 'tearDownFunc')  # TODO replace?
                if is_test_func_teardown:
                    finalizers.append(args)
                else:
                    scheduler.report(*args)
            break
    return res


nose.util.try_run.__code__ = wrapped_try_run.__code__


def find_setup_and_teardown(item):
    def find_func(obj, kind, names):
        for name in names:
            func = getattr(obj, name, None)
            if func is not None:
                return [(kind, func)]
        return []

    funcs = []
    if isinstance(item, FunctionTestCase):
        funcs = \
            find_func(item.test, 'setup', ('setup', 'setUp', 'setUpFunc')) + \
            find_func(item.test, 'teardown', ('teardown', 'tearDown', 'tearDownFunc'))

    res = []
    for kind, func in funcs:
        location = to_function_location(func)
        res.append(scheduler.collect(kind, location))
    return res


# ======================================================================================
# HELPERS
# ======================================================================================


def to_function_location(func, context=None):
    file = os.path.relpath(inspect.getfile(func), settings.runner_root)
    name = inspect.getmodule(func).__name__ + '::' + func.__qualname__
    _, line = inspect.getsourcelines(func)
    return Location(file, name, line)


def to_failure(exc_info):
    if exc_info is None:
        return None
    exc_type, exc_obj, exc_tb = exc_info
    return Failure(exc_type.__name__, str(exc_obj))

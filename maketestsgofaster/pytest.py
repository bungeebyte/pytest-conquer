import os.path
import inspect
import time
import sys
from collections import defaultdict

import pytest
try:
    from _pytest.nodes import Node
except ImportError:
    from _pytest.main import Node
from _pytest import python

from maketestsgofaster import logger
from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.settings import Settings
from maketestsgofaster.cloud.scheduler import Scheduler
from maketestsgofaster.model import Failure, Location

settings = None
scheduler = None
create_scheduler = lambda settings: Scheduler(settings)  # noqa: E731


# ======================================================================================
# SETUP
# ======================================================================================


def pytest_configure(config):
    logger.debug('loading maketestsgofaster')
    global scheduler, settings
    if tuple(map(int, (pytest.__version__.split('.')))) < (3, 0, 5):
        raise SystemExit('Sorry, maketestsgofaster requires at least pytest 3.0\n')

    settings = Settings(Env.create())
    settings.runner_name = 'pytest'
    for plugin, dist in config.pluginmanager.list_plugin_distinfo():
        settings.runner_plugins.add((dist.project_name, dist.version))
    settings.runner_root = str(config.rootdir)
    settings.runner_version = pytest.__version__
    scheduler = create_scheduler(settings)


# ======================================================================================
# COLLECTION
# ======================================================================================


class ScheduledList:
    def __init__(self):
        self.items = []
        self.index = 0
        self.items_by_file = defaultdict(list)

    def collect_test(self, item):
        fixtures = []
        for _, fixturedef in sorted(item._fixtureinfo.name2fixturedefs.items()):
            if fixturedef[0].baseid == '':  # means it's an artificial fixture for @pytest.mark.parametrize
                continue
            location = to_function_location(fixturedef[0].func)
            fixtures.append(scheduler.collect('fixture', location))

        file = os.path.relpath(item.fspath.strpath, settings.runner_root)
        name = '::'.join(item.nodeid.split('::')[1:])
        _, line = inspect.getsourcelines(item._obj)
        location = Location(file, name, line)
        scheduler.collect('test', location, fixtures)
        self.items_by_file[file].append(item)

    def __iter__(self):
        return self

    def __next__(self):
        next = self.__getitem__(self.index)
        if not next:
            raise StopIteration()
        self.index += 1
        return next

    def __len__(self):
        # '+ 1' because otherwise pytest won't try to fetch the 'nextitem'
        # and start calling the teardown methods prematurely.
        return len(self.items) + 1

    def __getitem__(self, key):
        if key >= len(self.items):
            self.__fetch_next()
        if key < len(self.items):
            return self.items[key]
        return None

    def __fetch_next(self):
        next_file = scheduler.next_file()
        if next_file:
            self.items.extend(self.items_by_file[next_file])


# Replace collected test items with `ScheduledList`.
# This way they can be loaded dynamically.
@pytest.hookimpl(hookwrapper=True)
def pytest_collection_modifyitems(session, config, items):
    yield  # let other plugins go first
    scheduled_list = ScheduledList()
    for item in items:
        scheduled_list.collect_test(item)
    session.items = scheduled_list


# ======================================================================================
# TEST REPORTING
# ======================================================================================


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()

    file = report.nodeid.split('::')[0]
    name = item.nodeid.replace(file + '::', '')
    line = report.location[1]
    location = Location(file, name, line + 1)

    def report_test(failure=None):
        status = report.outcome or 'passed'
        time = report.duration
        scheduler.report('test', location, status, time, failure)

    def send_report():
        failure = None
        if call.excinfo:
            exc_info = (call.excinfo.type, call.excinfo.value, call.excinfo.tb)
            failure = to_failure(exc_info)
        report_test(failure)

    if report.when == 'call':
        send_report()
    elif report.when == 'setup':
        if report.skipped:
            report_test()
        elif report.failed:
            report_test()


# ======================================================================================
# FIXTURE REPORTING
# ======================================================================================


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    start = time.time()

    result = yield  # actual setup

    if fixturedef.baseid == '':  # means it's an artificial fixture for @pytest.mark.parametrize
        return

    location = to_function_location(fixturedef.func)
    status = 'error' if result.excinfo else 'passed'
    failure = to_failure(result.excinfo)
    scheduler.report('fixture', location, status, time.time() - start, failure)


# ======================================================================================
# SETUP / TEARDOWN COLLECTION & REPORTING
# ======================================================================================


# Overwrite `_getcustomclass` to swap default implementations with custom ones
# that hook into setup and teardown procedures.

_getcustomclass = Node._getcustomclass


def getcustomclass(self, name):
    from maketestsgofaster.pytest import CustomClass, CustomFunction
    if name is 'Class':
        return CustomClass
    if name is 'Function':
        return CustomFunction
    return _getcustomclass(self, name)


Node._getcustomclass = getcustomclass


# Return a custom `Module` in order to hook into setup and teardown procedures.
@pytest.hookimpl(tryfirst=True)
def pytest_pycollect_makemodule(path, parent):
    if path.basename == '__init__.py':
        return python.Package(path, parent)
    return CustomModule(path, parent)


# Mixin that wraps default setup and teardown (finalizers) procedures.
class SetupReporting():
    def setup(self):
        func_location = self.setup_func_loc()
        start = time.time()
        try:
            self.run_setup()  # actual setup
        except Exception:
            if func_location:
                failure = to_failure(sys.exc_info())
                scheduler.report('setup', func_location, 'failed', time.time() - start, failure)
            raise
        if func_location:
            scheduler.report('setup', func_location, 'passed', time.time() - start, None)

    def addfinalizer(self, fin):
        def wrapped_teardown():
            func_location = self.teardown_func_loc()
            start = time.time()
            try:
                fin()  # actual teardown
            except Exception:
                failure = to_failure(sys.exc_info())
                scheduler.report('teardown', func_location, 'failed', time.time() - start, failure)
                raise
            scheduler.report('teardown', func_location, 'passed', time.time() - start, None)
        python.PyCollector.addfinalizer(self, wrapped_teardown)


class CustomModule(SetupReporting, python.Module):
    def run_setup(self):
        python.Module.setup(self)

    def setup_func_loc(self):
        func = python._get_xunit_func(self.obj, 'setUpModule') or \
            python._get_xunit_func(self.obj, 'setup_module')
        return to_function_location(func, self.obj)

    def teardown_func_loc(self):
        func = python._get_xunit_func(self.obj, 'tearDownModule') or \
            python._get_xunit_func(self.obj, 'teardown_module')
        return to_function_location(func, self.obj)


class CustomClass(SetupReporting, python.Class):
    def run_setup(self):
        python.Class.setup(self)

    def setup_func_loc(self):
        func = python._get_xunit_func(self.obj, 'setup_class')
        return to_function_location(func, self.obj)

    def teardown_func_loc(self):
        func = python._get_xunit_func(self.obj, 'teardown_class')
        return to_function_location(func, self.obj)


class CustomFunction(SetupReporting, python.Function):
    def __init__(self, *args, **kwargs):
        super(CustomFunction, self).__init__(*args, **kwargs)

    def run_setup(self):
        python.Function.setup(self)

    def teardown_func_loc(self):
        return self.lifecycle_func('teardown_function', 'teardown_method')

    def setup_func_loc(self):
        return self.lifecycle_func('setup_function', 'setup_method')

    def lifecycle_func(self, func_name, meth_name):
        if hasattr(self, '_preservedparent'):
            obj = self._preservedparent
        elif isinstance(self.parent, python.Instance):
            obj = self.parent.newinstance()
            self.obj = self._getobj()
        else:
            obj = self.parent.obj

        if inspect.ismethod(self.obj):
            setup_name = meth_name
        else:
            setup_name = func_name

        # TODO: _get_xunit_setup_teardown?
        func = python._get_xunit_func(obj, setup_name)
        return to_function_location(func, self.obj)


# ======================================================================================
# HELPERS
# ======================================================================================


def to_function_location(func, obj=None):
    if func:
        file = os.path.relpath(inspect.getfile(func), settings.runner_root)
        name = func.__name__
        if inspect.isclass(obj):
            for cls in obj.__qualname__.split('.')[::-1]:
                name = cls + '::' + name
        elif inspect.ismethod(obj):
            for cls in obj.__qualname__.split('.')[:-1][::-1]:
                name = cls + '::()::' + name
        _, line = inspect.getsourcelines(func)
        return Location(file, name, line)


def to_failure(exc_info):
    if exc_info is None:
        return None
    exc_type, exc_obj, exc_tb = exc_info
    return Failure(exc_type.__name__, str(exc_obj))

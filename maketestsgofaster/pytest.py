import os.path
import inspect
import multiprocessing
import sys
import time
from collections import defaultdict

import pytest

from maketestsgofaster.cloud.env import Env
from maketestsgofaster.cloud.scheduler import Scheduler
from maketestsgofaster.cloud.settings import Capability, Settings
from maketestsgofaster.model import Failure, Location


settings = None
scheduler = None
manager = multiprocessing.Manager()
create_scheduler = lambda settings: Scheduler(settings)  # noqa: E731


# ======================================================================================
# SETUP
# ======================================================================================


def pytest_configure(config):
    global scheduler, settings

    if tuple(map(int, (pytest.__version__.split('.')))) < (3, 0, 5):
        raise SystemExit('Sorry, maketestsgofaster requires at least pytest 3.0\n')

    create_settings(config)
    if settings.plugin_enabled():
        scheduler = create_scheduler(settings)


def create_settings(config):
    global settings
    settings = Settings(Env.create())
    settings.client_capabilities = [
        Capability.Fixtures,
        Capability.LifecycleTimings,
        Capability.SplitByFile,
    ]
    settings.runner_name = 'pytest'
    for plugin, dist in config.pluginmanager.list_plugin_distinfo():
        settings.runner_plugins.add((dist.project_name, dist.version))
    settings.runner_root = str(config.rootdir)
    settings.runner_version = pytest.__version__


# ======================================================================================
# COLLECTION
# ======================================================================================


# Replace collected test items with `ScheduledList`.
# This way they can be loaded dynamically.
@pytest.hookimpl(hookwrapper=True)
def pytest_collection_modifyitems(session, config, items):
    yield  # let other plugins go first

    if not settings.plugin_enabled():
        return

    scheduled_list = ScheduledList()
    for item in items:
        scheduled_list.collect_test(item)
    session.items = scheduled_list


class ScheduledList:
    def __init__(self):
        self.items = []
        self.index = 0
        self.items_by_file = defaultdict(list)

    def collect_test(self, item):
        fixtures = []
        for _, fixturedef in sorted(item._fixtureinfo.name2fixturedefs.items()):
            location = to_function_location(fixturedef[0].func)
            if is_artifical_fixture(fixturedef[0], location):
                continue
            fixtures.append(scheduler.collect('fixture', location))

        file = os.path.relpath(item.fspath.strpath, settings.runner_root)
        name = '::' \
            .join(item.nodeid.split('::')[1:]) \
            .replace('::()::', '::')  # the format was changed in pytest 4.x
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


# ======================================================================================
# TEST REPORTING
# ======================================================================================


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()

    if not settings.plugin_enabled():
        return report

    file = report.nodeid.split('::')[0]
    name = item.nodeid \
        .replace(file + '::', '') \
        .replace('::()::', '::')  # the format was changed in pytest 4.x
    line = report.location[1]
    location = Location(file, name, line + 1)

    def report_test(failure=None):
        status = report.outcome or 'passed'
        time = report.duration
        scheduler.report('test', location, status, time, failure)

    if report.when == 'call':
        failure = None
        if call.excinfo:
            exc_info = (call.excinfo.type, call.excinfo.value, call.excinfo.tb)
            failure = to_failure(exc_info)
        report_test(failure)
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

    if not settings.plugin_enabled():
        return

    location = to_function_location(fixturedef.func)

    if is_artifical_fixture(fixturedef, location):
        return

    status = 'error' if result.excinfo else 'passed'
    failure = to_failure(result.excinfo)
    scheduler.report('fixture', location, status, time.time() - start, failure)


# ======================================================================================
# SETUP / TEARDOWN REPORTING
# ======================================================================================


@pytest.hookimpl(tryfirst=True)
def pytest_make_collect_report(collector):
    if not settings.plugin_enabled():
        return

    if not hasattr(collector, 'obj'):
        return
    obj = collector.obj

    if inspect.isclass(obj):
        add_introspection(obj, 'setup_class', 'setup')
        add_introspection(obj, 'setup_method', 'setup')
        add_introspection(obj, 'teardown_class', 'teardown')
        add_introspection(obj, 'teardown_method', 'teardown')

    if inspect.ismodule(obj):
        add_introspection(obj, 'setup_function', 'setup')
        add_introspection(obj, 'setup_module', 'setup')
        add_introspection(obj, 'setUpModule', 'setup')
        add_introspection(obj, 'teardown_function', 'teardown')
        add_introspection(obj, 'teardown_module', 'teardown')
        add_introspection(obj, 'tearDownModule', 'teardown')


def add_introspection(obj, name, type):
    if not hasattr(obj, name):
        return
    func = getattr(obj, name)
    if hasattr(func, '__wrapped__'):
        func = func.__wrapped__
    func_loc = to_function_location(func, obj)
    scheduler.collect(type, func_loc)
    wrapped_func = wrap_with_report_func(func, func_loc, type)
    wrapped_func.__wrapped__ = func
    setattr(obj, name, wrapped_func)


def wrap_with_report_func(func, func_loc, type):
    def wrapper(arg1=None, arg2=None):
        start = time.time()
        try:
            arg_count = func.__code__.co_argcount
            if inspect.ismethod(func):
                arg_count -= 1
            if arg_count == 0:
                func()
            elif arg_count == 1:
                func(arg1)
            else:
                func(arg1, arg2)
        except Exception:
            if func_loc:
                failure = to_failure(sys.exc_info())
                scheduler.report(type, func_loc, 'failed', time.time() - start, failure)
            raise
        if func_loc:
            scheduler.report(type, func_loc, 'passed', time.time() - start, None)
    return wrapper


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
                name = cls + '::' + name
        _, line = inspect.getsourcelines(func)
        return Location(file, name, line)


def to_failure(exc_info):
    if exc_info is None:
        return None
    exc_type, exc_obj, exc_tb = exc_info
    return Failure(exc_type.__name__, str(exc_obj))


def is_artifical_fixture(fixturedef, location):
    # means it's an artificial fixture for @pytest.mark.parametrize
    if fixturedef.baseid == '':
        return True
    # means it's an artificial setup/teardown fixture (pytest 4+)
    if location.name == 'xunit_setup_class_fixture' or \
            location.name == 'xunit_setup_function_fixture' or \
            location.name == 'xunit_setup_method_fixture' or \
            location.name == 'xunit_setup_module_fixture':
        return True
    return False

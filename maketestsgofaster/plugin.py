import os.path
import os
import inspect
import multiprocessing
import sys
import threading
import traceback
import uuid
from collections import defaultdict
from datetime import datetime

import pytest
from _pytest import main

from maketestsgofaster.env import Env
from maketestsgofaster.model import Failure, Location, SuiteItem, ReportItem
from maketestsgofaster.scheduler import Scheduler
from maketestsgofaster.settings import Settings
from maketestsgofaster.terminal import ParallelTerminalReporter


manager = multiprocessing.Manager()
report_items = manager.dict()
settings = None
scheduler = None
suite_items = []
suite_item_locations = set()
suite_item_file_size_by_file = {}
reporter = None
tests_by_file = defaultdict(list)
worker_id = None


# ======================================================================================
# SETUP
# ======================================================================================


def pytest_addoption(parser):
    group = parser.getgroup('pytest-mtgf')

    workers_help = 'Set the number of workers. Default is 1, to use all CPU cores set to \'max\'.'
    group.addoption('--w', '--workers', action='store', default='1', dest='workers', help=workers_help)


@pytest.hookimpl(trylast=True)  # we need to wait for the 'terminalreporter' to be loaded
def pytest_configure(config):
    global reporter, scheduler, settings

    settings = create_settings(config)

    if settings.plugin_enabled():
        if tuple(map(int, (pytest.__version__.split('.')))) < (3, 0, 5):
            raise SystemExit('Sorry, maketestsgofaster requires at least pytest 3.0.5\n')

        scheduler = Scheduler(settings)

        # replace the builtin reporter with our own that handles concurrency better
        builtin_reporter = config.pluginmanager.get_plugin('terminalreporter')
        if builtin_reporter:
            reporter = ParallelTerminalReporter(builtin_reporter, manager)
            config.pluginmanager.unregister(builtin_reporter)
            config.pluginmanager.register(reporter, 'terminalreporter')


def create_settings(config):
    plugin_args = {
        'workers': config.option.workers,
    }

    res = Settings(Env.create(), plugin_args)

    res.runner_name = 'pytest'
    for plugin, dist in config.pluginmanager.list_plugin_distinfo():
        res.runner_plugins.add((dist.project_name, dist.version))
    res.runner_root = str(config.rootdir)
    res.runner_version = pytest.__version__

    return res


# ======================================================================================
# EXECUTION
# ======================================================================================


def pytest_runtestloop(session):
    if not settings.plugin_enabled():
        return main.pytest_runtestloop(session)

    threads = []
    no_of_workers = settings.plugin_workers
    for i in range(no_of_workers):
        t = Worker(args=[session])
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    return True


class Worker(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.session = kwargs['args'][0]
        self.id = str(uuid.uuid4())

    def run(self):
        schedule = scheduler.init(suite_items)
        while schedule.items:
            pid = self.run_schedule(schedule)
            schedule = scheduler.next(report_items.get(pid, []))

    def run_schedule(self, schedule):
        tests = []
        items = schedule.items
        for i, item in enumerate(items):
            tests.extend(tests_by_file[item.file])
        proc = Process(args=[tests, self.session])
        proc.start()
        proc.join()
        if proc.exception:
            print('\033[91m' + 'INTERNAL ERROR:')
            print(proc.exception + '\033[0m')
        reporter.pytest_runtest_logreport(None)  # force logs of the process to print
        return proc.id


class Process(multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self.id = uuid.uuid4()
        self.reader, self.writer = multiprocessing.Pipe()
        self.tests = kwargs['args'][0]
        self.session = kwargs['args'][1]
        self.err = None

    def run(self):
        try:
            for i, test in enumerate(self.tests):
                next_test = self.tests[i + 1] if i + 1 < len(self.tests) else None
                test.config.hook.pytest_runtest_protocol(item=test, nextitem=next_test)
        except Exception:
            self.writer.send(traceback.format_exc())

    @property
    def exception(self):
        if self.reader.poll():
            self.err = self.reader.recv()
        return self.err


# ======================================================================================
# COLLECTION
# ======================================================================================


@pytest.hookimpl(hookwrapper=True)
def pytest_collection_modifyitems(session, config, items):
    yield  # let other plugins go first

    if not settings.plugin_enabled():
        return

    for item in items:
        collect_test(item)


def collect_test(item):
    _, line = inspect.getsourcelines(item._obj)
    location = item_to_location(item, line)
    fixtures = collect_fixtures(item)
    tags = [mark.name for mark in item.iter_markers()]
    collect_item(SuiteItem('test', location, deps=fixtures, tags=tags))
    tests_by_file[location.file].append(item)


def collect_fixtures(item):
    fixtures = []
    for _, fixturedef in sorted(item._fixtureinfo.name2fixturedefs.items()):
        location = func_to_location(fixturedef[0].func)
        if is_artifical_fixture(fixturedef[0], location):
            continue

        tags = []
        if hasattr(fixturedef[0].func, 'pytestmark'):
            for mark in fixturedef[0].func.pytestmark:
                tags.append(mark.name)

        fixtures.append(collect_item(SuiteItem('fixture', location, tags=tags)))
    return fixtures


# ======================================================================================
# TEST REPORTING
# ======================================================================================


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()

    if not settings.plugin_enabled():
        return report

    line = report.location[1] + 1
    location = item_to_location(report, line)

    def report_test(failure=None):
        status = report.outcome or 'passed'
        report_item('test', location, status, call.start, call.stop, failure)

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
def pytest_fixture_setup(fixturedef):
    start = datetime.utcnow()
    result = yield  # actual setup
    report_fixture_step('setup', start, fixturedef, result)


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_post_finalizer(fixturedef):
    start = datetime.utcnow()
    result = yield  # actual teardown
    report_fixture_step('teardown', start, fixturedef, result)


def report_fixture_step(type, started_at, fixturedef, result):
    if not settings.plugin_enabled():
        return

    print(fixturedef.__dict__)

    location = func_to_location(fixturedef.func)

    if is_artifical_fixture(fixturedef, location):
        return

    status = 'error' if result.excinfo else 'passed'
    failure = to_failure(result.excinfo)
    report_item(type, location, status, started_at, datetime.utcnow(), failure)


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
    func_loc = func_to_location(func, obj)
    collect_item(SuiteItem(type, func_loc))
    wrapped_func = wrap_with_report_func(func, func_loc, type)
    wrapped_func.__wrapped__ = func
    setattr(obj, name, wrapped_func)


def wrap_with_report_func(func, func_loc, type):
    def wrapper(arg1=None, arg2=None):
        start = datetime.utcnow()
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
                report_item(type, func_loc, 'failed', start, datetime.utcnow(), failure)
            raise
        if func_loc:
            report_item(type, func_loc, 'passed', start, datetime.utcnow(), None)
    return wrapper


# ======================================================================================
# HELPERS
# ======================================================================================


def collect_item(item):
    def collect(item):
        if item.location in suite_item_locations:
            return False  # prevents duplicates
        suite_items.append(item)
        suite_item_locations.add(item.location)
        return True

    if collect(item):
        file = item.location.file
        file_size = suite_item_file_size_by_file.get(file, None)
        if not os.path.isdir(file) and file_size is None:
            file_size = os.path.getsize(file)
            suite_item_file_size_by_file[file] = file_size
        collect(SuiteItem('file', Location(file), size=file_size))

        cls = item.location.cls
        if cls:
            collect(SuiteItem('class', Location(file, cls)))

    return item


# This is called from multiple subprocesses, so we need to manage the data by process ID.
def report_item(type, location, status, start, end, failure):
    items = []
    process_id = multiprocessing.current_process().id
    if process_id in report_items:
        items = report_items[process_id]
    worker_id = threading.current_thread().id
    items.append(ReportItem(type, location, status, failure, start, end, worker_id, process_id))
    report_items[process_id] = items  # only be reassigning will the data be synced


def func_to_location(func, obj=None):
    if func:
        abs_file = inspect.getfile(obj) if obj else inspect.getfile(func)
        rel_file = os.path.relpath(abs_file, settings.runner_root)
        name = func.__name__
        classes = []
        if inspect.isclass(obj):
            for cls in obj.__qualname__.split('.')[::-1]:
                classes.append(cls)
        elif inspect.ismethod(obj):
            for cls in obj.__qualname__.split('.')[:-1][::-1]:
                classes.append(cls)
        _, line = inspect.getsourcelines(func)
        cls = '.'.join(classes[::-1]) if classes else None
        return Location(rel_file, cls, name, line)


def item_to_location(item, line):
    nodeid = item.nodeid \
        .replace('::()::', '::') \
        .split('::')
    file = nodeid.pop(0)
    name = nodeid.pop()
    cls = '.'.join(nodeid) if nodeid else None
    return Location(file, cls, name, line)


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
    if location.func == 'xunit_setup_class_fixture' or \
            location.func == 'xunit_setup_function_fixture' or \
            location.func == 'xunit_setup_method_fixture' or \
            location.func == 'xunit_setup_module_fixture':
        return True
    return False

import asyncio
import functools
import os.path
import os
import inspect
import sys
import threading
import uuid
import itertools
from collections import defaultdict
from datetime import datetime

import pytest
from _pytest import main

from testandconquer.client import Client
from testandconquer.model import Failure, Location, SuiteItem, Report, ReportItem, Tag
from testandconquer.scheduler import Scheduler
from testandconquer.settings import Settings


fatal_error = None
report_items_by_worker = {}
schedulers = []
settings = None
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
    group = parser.getgroup('pytest-conquer')

    conquer_help = 'Divide and conquer tests.'
    group.addoption('--conquer', action='store_true', default=None, dest='enabled', help=conquer_help)

    workers_help = "Set the number of workers. Default is 1, to use all CPU cores set to 'max'."
    group.addoption('--w', '--workers', action='store', default=None, dest='workers', help=workers_help)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    global reporter, settings

    settings = create_settings(config)

    if settings.enabled:
        if tuple(map(int, (pytest.__version__.split('.')))) < (3, 6, 0):
            raise SystemExit('Sorry, pytest-conquer requires at least pytest 3.6.0\n')

        if sys.version_info < (3, 6, 0):
            raise SystemExit('Sorry, pytest-conquer requires at least Python 3.6.0\n')


def create_settings(config):
    plugins = config.pluginmanager.list_plugin_distinfo()
    plugins.sort(key=lambda item: item[1].project_name)
    settings = Settings({
        'enabled': config.option.enabled,
        'runner_name': 'pytest',
        'runner_plugins': [(dist.project_name, dist.version) for plugin, dist in plugins],
        'runner_root': str(config.rootdir),
        'runner_version': pytest.__version__,
        'workers': config.option.workers,
    })
    settings.init_from_file('pytest.ini')
    return settings


# ======================================================================================
# EXECUTION
# ======================================================================================


def pytest_runtestloop(session):
    if not settings.enabled:
        return main.pytest_runtestloop(session)

    if session.testsfailed and not session.config.option.continue_on_collection_errors:
        raise session.Interrupted('{} errors during collection'.format(session.testsfailed))

    if session.config.option.collectonly:
        return True

    threads = []
    no_of_workers = settings.client_workers
    for i in range(no_of_workers):
        t = Worker(args=[session, settings])
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    return True


class Worker(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, name=str(uuid.uuid4()), *args, **kwargs)
        self.session = kwargs['args'][0]
        self.settings = kwargs['args'][1]

    def run(self):
        global fatal_error
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.run_task())
            loop.close()
        except Exception:
            fatal_error = True
            raise

    async def run_task(self):
        global suite_items, schedulers
        # init client
        client = Client(settings)
        client.subscribe(self.settings)

        # init scheduler
        scheduler = Scheduler(self.settings, client, suite_items, self.name)
        schedulers.append(scheduler)

        # connect to server
        await client.start()

        # work through test items
        while not scheduler.done:
            pending_at = datetime.utcnow()
            schedule = await scheduler.next()
            started_at = datetime.utcnow()
            report_items = self.execute_schedule(schedule)
            finished_at = datetime.utcnow()
            await scheduler.report(Report(report_items, pending_at, started_at, finished_at))

        # wrap things up
        await scheduler.stop()
        await client.stop()

    def execute_schedule(self, schedule):
        global report_items_by_worker
        report_items_by_worker[self.name] = []

        res = []
        for batch in schedule.batches:
            files = [item.file for item in batch.items]
            tests = list(itertools.chain(*[tests_by_file[f] for f in files]))
            for i, test in enumerate(tests):
                next_test = tests[i + 1] if i + 1 < len(tests) else None
                test.config.hook.pytest_runtest_protocol(item=test, nextitem=next_test)
            res.extend(report_items_by_worker[self.name])

        return res


# report internal error properly
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    global fatal_error
    if fatal_error:
        pytest.exit('', 1)


# ======================================================================================
# COLLECTION
# ======================================================================================


@pytest.hookimpl(tryfirst=True)  # has to be first or the introspection doesn't work
def pytest_make_collect_report(collector):
    if not settings.enabled:
        return

    obj = None
    try:
        # this can fail if there is a syntax error in the module for example
        if not hasattr(collector, 'obj'):
            return
        obj = collector.obj
    except:  # noqa: E722
        pass  # we'll let pytest deal with it

    if inspect.isclass(obj):
        collect_class(obj)
    elif inspect.ismodule(obj):
        collect_module(obj)


@pytest.hookimpl(hookwrapper=True)
def pytest_collection_modifyitems(session, config, items):
    yield  # let other plugins go first

    if not settings.enabled:
        return

    for node in items:
        collect_test(node)


def collect_test(node):
    location = node_to_location(node)
    fixtures = collect_fixtures(node)
    collect_item(SuiteItem('test', location, deps=fixtures, tags=parse_tags(node.obj)))
    tests_by_file[location.file].append(node)


def collect_fixtures(node):
    fixtures = []
    if hasattr(node, '_fixtureinfo'):
        for _, fixturedef in sorted(node._fixtureinfo.name2fixturedefs.items()):
            fixture_fn = fixturedef[0].func
            location = func_to_location(fixture_fn)
            if is_artifical_fixture(fixturedef[0], location):
                continue
            fixtures.append(collect_item(SuiteItem('fixture', location, tags=parse_tags(fixture_fn))))
    return fixtures


def collect_class(obj):
    location = func_to_location(None, obj)
    collect_item(SuiteItem('class', location, tags=parse_tags(obj)))

    add_introspection(obj, ['setup_class'], 'setup', 'class')
    add_introspection(obj, ['setup_method'], 'setup', 'method')
    add_introspection(obj, ['teardown_class'], 'teardown', 'class')
    add_introspection(obj, ['teardown_method'], 'teardown', 'method')


def collect_module(obj):
    add_introspection(obj, ['setup_function'], 'setup', 'function')
    add_introspection(obj, ['setUpModule', 'setup_module'], 'setup', 'module')
    add_introspection(obj, ['teardown_function'], 'teardown', 'function')
    add_introspection(obj, ['tearDownModule', 'teardown_module'], 'teardown', 'module')


def add_introspection(obj, names, type, scope):
    for name in names:
        if not hasattr(obj, name):
            continue
        func = getattr(obj, name)
        if hasattr(func, '__wrapped__'):
            func = func.__wrapped__
        func_loc = func_to_location(func, obj)
        collect_item(SuiteItem(type, func_loc, scope=scope, tags=parse_tags(func)))
        wrapped_func = wrap_with_report_func(func, func_loc, type)
        wrapped_func.__wrapped__ = func
        setattr(obj, name, wrapped_func)
        break  # stop after the first one


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
# REPORTING
# ======================================================================================


# we wrap the test run so we know when it started/finished
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    item.__start_time = datetime.utcnow()
    yield
    item.__finish_time = datetime.utcnow()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()

    if not settings.enabled:
        return

    location = node_to_location(item)

    def report_test(failure=None):
        status = report.outcome or 'passed'
        report_item('test', location, status,
                    getattr(item, '__start_time', None), getattr(item, '__finish_time', None), failure)

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


# we wrap the setup so we know when it started
@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef):
    start = datetime.utcnow()
    result = yield  # actual setup
    report_fixture_step('setup', start, fixturedef, result)


# we wrap the teardown so we know when it started
@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_post_finalizer(fixturedef):
    start = datetime.utcnow()
    result = yield  # actual teardown
    report_fixture_step('teardown', start, fixturedef, result)


def report_fixture_step(type, started_at, fixturedef, result):
    if not settings.enabled:
        return

    finished_at = datetime.utcnow()
    location = func_to_location(fixturedef.func)

    if is_artifical_fixture(fixturedef, location):
        return

    status = 'error' if result.excinfo else 'passed'
    failure = to_failure(result.excinfo)
    report_item(type, location, status, started_at, finished_at, failure)


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

    return item


def report_item(type, location, status, start, end, failure):
    worker_id = threading.current_thread().name
    report_items_by_worker[worker_id].append(ReportItem(type, location, status, failure, start, end))


def node_to_location(node):
    func = node.obj
    parent = node
    obj = None
    while parent is not None and not inspect.ismodule(obj) and not inspect.isclass(obj):
        parent = parent.parent
        obj = parent.obj
    location = func_to_location(func, obj)

    nodeid = node.nodeid \
        .replace('::()::', '::') \
        .split('::')
    name = nodeid.pop()

    return location._replace(func=name)


# This function is rather expensive so we only want to run it once per function
@functools.lru_cache(maxsize=None)
def func_to_location(func, obj=None):
    abs_file = inspect.getfile(obj) if obj else inspect.getfile(func)
    rel_file = os.path.relpath(abs_file, settings.runner_root)
    name = func.__name__ if func else None
    classes = []
    if inspect.isclass(obj):
        for cls in obj.__qualname__.split('.')[::-1]:
            classes.append(cls)
    elif inspect.ismethod(obj):
        for cls in obj.__qualname__.split('.')[:-1][::-1]:
            classes.append(cls)
    _, line = inspect.getsourcelines(func or obj)
    cls = '.'.join(classes[::-1]) if classes else None
    module = inspect.getmodule(obj or func).__name__
    return Location(rel_file, module, cls, name, line)


def parse_tags(obj):
    marks = []

    if hasattr(obj, 'pytestmark'):
        marks.extend([m for m in obj.pytestmark if getattr(m, 'name', None) == 'conquer'])
    elif hasattr(obj, 'conquer'):  # before pytest 3.6
        marks.append(getattr(obj, 'conquer'))

    tags = []
    for mark in marks:
        if mark is None:
            continue
        group = mark.kwargs.get('group', None)
        singleton = mark.kwargs.get('singleton', None) is True
        tags.append(Tag(group, singleton))

    # special case for pytest before 3.6:
    # remove tags from function if the class has the same
    if inspect.ismethod(obj):
        cls = obj.__self__
        if parse_tags(cls) == tags:
            return []

    return tags


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

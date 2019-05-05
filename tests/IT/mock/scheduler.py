from multiprocessing import Manager

from testandconquer.scheduler import Scheduler
from testandconquer.model import Schedule, ScheduleItem

from tests.IT.mock.settings import MockSettings


manager = Manager()
synchronization = dict(manager=manager)


class MockScheduler(Scheduler):
    def __init__(self, env):
        self.settings = MockSettings(env)
        self._suite_items = []
        self._suite_files = manager.list()
        self._report_items = manager.list()
        synchronization['lock'] = manager.Lock()

    def init(self):
        pass

    def start(self, suite_items):
        with synchronization['lock']:
            if not self._suite_files:
                self._suite_items = suite_items
                self._suite_files = list(set([i.location.file for i in suite_items]))
        return self.__next()

    def next(self, report_items):
        with synchronization['lock']:
            self._report_items.extend(report_items)
        return self.__next()

    @property
    def suite_items(self):
        return self.__sorted(self.__fixed_suite(self._suite_items))

    @property
    def report_items(self):
        return self.__sorted(self.__fixed_report(self._report_items))

    def __next(self):
        with synchronization['lock']:
            items = []
            if self._suite_files:
                items = [ScheduleItem(self._suite_files.pop(0))]
            return Schedule(items)

    def __fixed_report(self, report_items):
        items = []
        for item in report_items:
            item = item._replace(started_at=None, finished_at=None, process_id=None, worker_id=None)
            items.append(item)
        return items

    def __fixed_suite(self, suite_items):
        items = []
        for item in suite_items:
            if item.type == 'file':
                item = item._replace(size=42)
            item = item._replace(tags=item.tags if item.tags else None)
            item = item._replace(deps=self.__fixed_suite(item.deps) if item.deps else None)
            items.append(item)
        return items

    def __sorted(self, items):
        return sorted(items, key=lambda item: (
            item.type,
            item.location.file.lower(),
            (item.location.cls or '').lower(),
            (item.location.func or '').lower()))

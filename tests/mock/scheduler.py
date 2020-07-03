import uuid
from multiprocessing import Manager

from testandconquer.model import Schedule, ScheduleItem


manager = Manager()
synchronization = dict(manager=manager)


class MockScheduler():
    def __init__(self, settings, client, suite_items, worker_id):
        self.done = False
        self.settings = settings
        self._suite_items = suite_items
        self.suite_files = manager.list()
        self._report_items = manager.list()
        self.suite_files = list(set([i.location.file for i in suite_items]))
        synchronization['lock'] = manager.Lock()

    async def stop(self):
        pass

    async def next(self):
        with synchronization['lock']:
            items = []
            if self.suite_files:
                items = [ScheduleItem(self.suite_files.pop(0))]
            else:
                self.done = True
            return Schedule(uuid.uuid1(), items)

    async def report(self, report):
        with synchronization['lock']:
            self._report_items.extend(report.items)

    @property
    def suite_items(self):
        return self.__sorted(self.__fixed_suite(self._suite_items))

    @property
    def report_items(self):
        return self.__sorted(self.__fixed_report(self._report_items))

    def __fixed_report(self, report_items):
        items = []
        for item in report_items:
            item = item._replace(started_at=None, finished_at=None)
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

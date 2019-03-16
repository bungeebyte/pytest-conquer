from collections import namedtuple
from multiprocessing import Manager

from maketestsgofaster.scheduler import Scheduler
from maketestsgofaster.model import Schedule, ScheduleItem


manager = Manager()
synchronization = dict(manager=manager)


class MockScheduler(Scheduler):
    def __init__(self, _settings):
        self._suite_items = []
        self._suite_files = manager.list()
        self._report_items = manager.list()
        synchronization['lock'] = manager.Lock()

    def init(self, suite_items):
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
        return self.__sorted(self.__fixed_file_size(self._suite_items))

    @property
    def report_items(self):
        return self.__sorted(self.__fixed_time(self._report_items))

    def __next(self):
        with synchronization['lock']:
            items = []
            if self._suite_files:
                items = [ScheduleItem(self._suite_files.pop(0))]
            return Schedule(items)

    def __fixed_time(self, report_items):
        items = []
        for item in report_items:
            if item.time > 0.0:
                asdict = item._asdict()
                asdict['time'] = 0.1
                items.append(namedtuple('ReportItem', asdict.keys())(**asdict))
            else:
                items.append(item)
        return items

    def __fixed_file_size(self, suite_items):
        items = []
        for item in suite_items:
            asdict = item._asdict()
            asdict['file_size'] = 42
            asdict['deps'] = self.__fixed_file_size(asdict['deps'])
            items.append(namedtuple('SuiteItem', asdict.keys())(**asdict))
        return items

    def __sorted(self, items):
        return sorted(items, key=lambda item: (item.type, item.location.file.lower(), item.location.name.lower()))

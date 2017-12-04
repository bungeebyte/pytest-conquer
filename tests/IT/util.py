from collections import namedtuple

from maketestsgofaster.cloud.scheduler import Scheduler


class MockScheduler(Scheduler):
    def __init__(self, settings):
        super().__init__(settings)
        self.items = None

    def next_file(self):
        if self.__get_files():
            return self.items.pop(0)

    def __get_files(self):
        if self.items is None:
            self.items = []
            for item in self.suite_builder.items:
                file = item.location.file
                if item.type == 'test' and file not in self.items:
                    self.items.append(file)
        return self.items

    def validate_settings(self, settings):
        pass


def round_time(report_items):
    items = []
    for item in report_items:
        if item.time > 0.0:
            asdict = item._asdict()
            asdict['time'] = 0.1
            items.append(namedtuple('ReportItem', asdict.keys())(**asdict))
        else:
            items.append(item)
    return items


def round_file_size(suite_items):
    items = []
    for item in suite_items:
        asdict = item._asdict()
        asdict['file_size'] = 42
        asdict['fixtures'] = round_file_size(asdict['fixtures'])
        items.append(namedtuple('SuiteItem', asdict.keys())(**asdict))
    return items

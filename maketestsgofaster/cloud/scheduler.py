import os.path

from maketestsgofaster import logger
from maketestsgofaster.cloud.bridge import Bridge
from maketestsgofaster.model import ReportItem, SuiteItem


class Scheduler:
    def __init__(self, settings):
        self.validate_settings(settings)
        self.index = 0
        self.schedule = None
        self.bridge = Bridge(settings)
        self.suite_builder = SuiteBuilder(settings)
        self.report_builder = ReportBuilder(settings)

    def collect(self, type, location, fixtures=[]):
        return self.suite_builder.add(type, location, fixtures)

    def report(self, type, location, status, time, details):
        return self.report_builder.add(type, location, status, time, details)

    def next_file(self):
        if not self.schedule:
            logger.debug('init schedule')
            self.schedule = self.bridge.init(self.suite_builder.items)
        if not self.schedule.items:
            logger.debug('no more items')
            return
        if self.index >= len(self.schedule.items):
            logger.debug('next schedule')
            self.schedule = self.bridge.next(self.report_builder.items)
            self.report_builder.reset()
            self.index = 0
        if not self.schedule.items:
            logger.debug('no more items')
            return
        file = self.schedule.items[self.index].file
        logger.debug('next file: %s', file)
        self.index += 1
        return file

    def validate_settings(self, settings):
        settings.validate()


class SuiteBuilder:
    def __init__(self, settings):
        self.items = []
        self.locations = set()
        self.file_size_by_file = {}

    def add(self, type, location, fixtures):
        file = location.file
        file_size = self.file_size_by_file.get(file, None)

        if not os.path.isdir(file) and file_size is None:
            file_size = os.path.getsize(file)
            self.file_size_by_file[file] = file_size

        item = SuiteItem(type, location, file_size, fixtures)

        if location not in self.locations:  # prevents duplicates
            self.items.append(item)
            self.locations.add(location)

        return item


class ReportBuilder:
    def __init__(self, settings):
        self.reset()

    def add(self, type, location, status, time, details):
        item = ReportItem(type, location, status, time, details)
        self.items.append(item)
        return item

    def reset(self):
        self.items = []

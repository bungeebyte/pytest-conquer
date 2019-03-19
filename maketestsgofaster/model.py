from collections import namedtuple

SuiteItem = \
    namedtuple('SuiteItem', ['type', 'location', 'file_size', 'deps'])

ReportItem = \
    namedtuple('ReportItem', ['type', 'location', 'status', 'error', 'started_at', 'finished_at', 'worker_id', 'process_id'])
ReportItem.__new__.__defaults__ = (None,) * len(ReportItem._fields)

Schedule = \
    namedtuple('Schedule', ['items'])

ScheduleItem = \
    namedtuple('ScheduleItem', ['file'])

Location = \
    namedtuple('Location', ['file', 'name', 'line'])

Failure = \
    namedtuple('Failure', ['type', 'message'])

from collections import namedtuple

SuiteItem = \
    namedtuple('SuiteItem', ['type', 'location', 'file_size', 'deps'])

ReportItem = \
    namedtuple('ReportItem', ['type', 'location', 'status', 'time', 'details'])

Schedule = \
    namedtuple('Schedule', ['items'])

ScheduleItem = \
    namedtuple('ScheduleItem', ['file'])

Location = \
    namedtuple('Location', ['file', 'name', 'line'])

Failure = \
    namedtuple('Failure', ['type', 'message'])

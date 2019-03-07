from collections import OrderedDict

from maketestsgofaster import logger
from maketestsgofaster.cloud.client import Client
from maketestsgofaster.model import Schedule, ScheduleItem


class Bridge:
    def __init__(self, settings):
        self.config = ConfigSerializer.serialize(settings)
        logger.debug('generated config: %s', self.config)
        self.client = Client(settings)

    def init(self, suite_items):
        logger.debug('initialising suite with %s item(s)', len(suite_items))
        suite_data = SuiteSerializer.serialize(self.config, suite_items)
        schedule_data = self.client.send('/suites', suite_data)
        return self.__parse_schedule(schedule_data)

    def next(self, report_items):
        logger.debug('submitting report with %s item(s)', len(report_items))
        report_data = ReportSerializer.serialize(self.config, report_items)
        schedule_data = self.client.send('/reports', report_data)
        return self.__parse_schedule(schedule_data)

    def __parse_schedule(self, data):
        tests_by_file = OrderedDict()
        for item in data['items']:
            tests_by_file.setdefault(item['file'], [])
            tests_by_file[item['file']].append(item['name'])
        items = [ScheduleItem(f) for f in tests_by_file.keys()]
        logger.debug('received schedule with %s item(s)', len(items))
        return Schedule(items)


class Serializer:

    @staticmethod
    def truncate(data, max_size):
        if data is None:
            return None
        return data[:max_size]


class ConfigSerializer:

    @staticmethod
    def serialize(settings):
        return {
            'build': {
                'dir': Serializer.truncate(settings.build_dir, 1024),
                'id': Serializer.truncate(settings.build_id, 64),
                'job': Serializer.truncate(settings.build_job, 64),
                'pool': settings.build_pool,
                'project': Serializer.truncate(settings.build_project, 1024),
                'url': Serializer.truncate(settings.build_url, 1024),
                'worker': Serializer.truncate(settings.build_worker, 256),
            },
            'client': {
                'capabilities': [c.value for c in settings.client_capabilities],
                'name': Serializer.truncate(settings.client_name, 64),
                'version': Serializer.truncate(settings.client_version, 32),
            },
            'platform': {
                'name': Serializer.truncate(settings.platform_name, 64),
                'version': Serializer.truncate(settings.platform_version, 32),
            },
            'runner': {
                'name': Serializer.truncate(settings.runner_name, 64),
                'plugins': [{
                    'name': Serializer.truncate(p[0], 64),
                    'version': Serializer.truncate(p[1], 64),
                } for p in settings.runner_plugins],
                'root': Serializer.truncate(settings.runner_root, 1024),
                'version': Serializer.truncate(settings.runner_version, 32),
            },
            'system': {
                'context': settings.system_context,
                'cpus': settings.system_cpus,
                'name': Serializer.truncate(settings.system_name, 64),
                'os': {
                    'name': Serializer.truncate(settings.system_os_name, 64),
                    'version': Serializer.truncate(settings.system_os_version, 32),
                },
                'ram': settings.system_ram,
            },
            'vcs': {
                'branch': Serializer.truncate(settings.vcs_branch, 1024),
                'pr': Serializer.truncate(settings.vcs_pr, 64),
                'repo': Serializer.truncate(settings.vcs_repo, 1024),
                'revision': Serializer.truncate(settings.vcs_revision, 64),
                'revision_message': Serializer.truncate(settings.vcs_revision_message, 1024),
                'tag': Serializer.truncate(settings.vcs_tag, 1024),
                'type': Serializer.truncate(settings.vcs_type, 64),
            },
        }


class SuiteSerializer:

    @staticmethod
    def serialize(config, suite_items):
        return {
            'config': config,
            'items': [SuiteSerializer.serialize_item(i) for i in suite_items],
        }

    @staticmethod
    def serialize_item(item):
        return {
            'type': Serializer.truncate(item.type, 1024),
            'file': Serializer.truncate(item.location.file, 1024),
            'file_size': item.file_size,
            'name': Serializer.truncate(item.location.name, 1024),
            'line': item.location.line,
            'fixtures': [SuiteSerializer.serialize_item(f) for f in item.fixtures],
        }


class ReportSerializer:

    @staticmethod
    def serialize(config, report_items):
        return {
            'config': config,
            'items': [ReportSerializer.serialize_item(i) for i in report_items],
        }

    @staticmethod
    def serialize_item(item):
        data = {
            'file': Serializer.truncate(item.location.file, 1024),
            'type': item.type,
            'name': Serializer.truncate(item.location.name, 1024),
            'line': item.location.line,
            'status': item.status,
            'time': item.time,
        }
        details = item.details
        if item.details:
            data['details'] = {
                'type': Serializer.truncate(details.type, 1024),
                'message': Serializer.truncate(details.message, 1024),
            }
        return data

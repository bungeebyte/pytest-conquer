from testandconquer import logger
from testandconquer.client import Client
from testandconquer.model import Schedule, ScheduleItem
from testandconquer.settings import Settings


class Scheduler:
    def __init__(self, args):
        self.settings = Settings(args)
        self.settings.validate()
        self.config = ConfigSerializer.serialize(self.settings)
        logger.debug('generated config: %s', self.config)
        self.client = Client(self.settings)

    def init(self, suite_items):
        logger.debug('initialising suite with %s item(s)', len(suite_items))
        suite_data = SuiteSerializer.serialize(self.config, suite_items)
        schedule_data = self.client.post('/suites', suite_data)
        return self.__parse_schedule(schedule_data)

    def next(self, report_items):
        logger.debug('submitting report with %s item(s)', len(report_items))
        report_data = ReportSerializer.serialize(self.config, report_items)
        schedule_data = self.client.post('/reports', report_data)
        return self.__parse_schedule(schedule_data)

    def __parse_schedule(self, data):
        schedule_items = []
        for item in data['items']:
            schedule_items.append(ScheduleItem(item['file']))
        logger.debug('received schedule with %s item(s)', len(schedule_items))
        return Schedule(schedule_items)


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
                'node': Serializer.truncate(settings.build_node, 256),
                'pool': settings.build_pool,
                'project': Serializer.truncate(settings.build_project, 1024),
                'url': Serializer.truncate(settings.build_url, 1024),
            },
            'client': {
                'capabilities': [c.value for c in settings.client_capabilities],
                'name': Serializer.truncate(settings.client_name, 64),
                'version': Serializer.truncate(settings.client_version, 32),
                'workers': settings.client_workers,
            },
            'platform': {
                'name': Serializer.truncate(settings.platform_name, 64),
                'version': Serializer.truncate(settings.platform_version, 32),
            },
            'runner': {
                'args': [Serializer.truncate(arg, 255) for arg in settings.runner_args],
                'name': Serializer.truncate(settings.runner_name, 64),
                'plugins': [{
                    'name': Serializer.truncate(p[0], 64),
                    'version': Serializer.truncate(p[1], 64),
                } for p in (settings.runner_plugins or [])],
                'root': Serializer.truncate(settings.runner_root, 1024),
                'version': Serializer.truncate(settings.runner_version, 32),
            },
            'system': {
                'context': settings.system_context,
                'cpus': settings.system_cpus,
                'os': {
                    'name': Serializer.truncate(settings.system_os_name, 64),
                    'version': Serializer.truncate(settings.system_os_version, 32),
                },
                'provider': Serializer.truncate(settings.system_provider, 64),
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
        data = {
            'type': item.type,
            'file': Serializer.truncate(item.location.file, 1024),
        }
        if item.location.func:
            data['func'] = Serializer.truncate(item.location.func, 1024)
        if item.size:
            data['file_size'] = item.size
        if item.location.module:
            data['module'] = Serializer.truncate(item.location.module, 1024)
        if item.location.cls:
            data['class'] = Serializer.truncate(item.location.cls, 1024)
        if item.location.line:
            data['line'] = item.location.line
        if item.tags:
            data['tags'] = [SuiteSerializer.serialize_tag(t) for t in item.tags]
        if item.deps:
            data['deps'] = [SuiteSerializer.serialize_fixture_ref(f) for f in item.deps]
        return data

    @staticmethod
    def serialize_tag(tag):
        data = {}
        if tag.group:
            data['group'] = Serializer.truncate(str(tag.group), 1024)
        if tag.singleton:
            data['singleton'] = True
        return data

    @staticmethod
    def serialize_fixture_ref(item):
        data = {
            'type': item.type,
            'file': Serializer.truncate(item.file, 1024),
            'func': Serializer.truncate(item.func, 1024),
            'line': item.line,
        }
        if item.module:
            data['module'] = Serializer.truncate(item.module, 1024)
        if item.cls:
            data['class'] = Serializer.truncate(item.cls, 1024)
        return data


class ReportSerializer:

    date_format = '%Y-%m-%dT%H:%M:%S.000Z'

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
            'type': str(item.type),
            'func': Serializer.truncate(item.location.func, 1024),
            'line': item.location.line,
            'status': item.status,
            'process_id': str(item.process_id),
            'worker_id': item.worker_id,
            'started_at': item.started_at.strftime(ReportSerializer.date_format),
            'finished_at': item.finished_at.strftime(ReportSerializer.date_format),
        }
        if item.location.module:
            data['module'] = Serializer.truncate(item.location.module, 1024)
        if item.location.cls:
            data['class'] = Serializer.truncate(item.location.cls, 1024)
        if item.error:
            data['error'] = {
                'type': Serializer.truncate(item.error.type, 1024),
                'message': Serializer.truncate(item.error.message, 1024),
            }
        return data

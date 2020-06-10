from testandconquer import logger
from testandconquer.client import MessageType
from testandconquer.model import Schedule, ScheduleItem
from testandconquer.settings import Capability


class Serializer:

    date_format = '%Y-%m-%dT%H:%M:%S.000Z'

    @staticmethod
    def serialize_config(*args, **kwargs):
        return ConfigSerializer.serialize(*args, **kwargs)

    @staticmethod
    def serialize_suite(*args, **kwargs):
        return SuiteSerializer.serialize(*args, **kwargs)

    @staticmethod
    def serialize_report(*args, **kwargs):
        return ReportSerializer.serialize(*args, **kwargs)

    @staticmethod
    def deserialize_schedule(*args, **kwargs):
        return ScheduleSerializer.deserialize(*args, **kwargs)

    @staticmethod
    def truncate(data, max_size):
        if data is None:
            return None
        return data[:max_size]


class ConfigSerializer:

    @staticmethod
    def serialize(settings, worker_id):
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
                'capabilities': [c.value for c in Capability],
                'messages': [t.value for t in MessageType],
                'name': Serializer.truncate(settings.client_name, 64),
                'version': Serializer.truncate(settings.client_version, 32),
                'workers': settings.client_workers,
                'worker_id': worker_id,
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
                'os': Serializer.truncate(settings.system_os_name, 64),
                'os_version': Serializer.truncate(settings.system_os_version, 32),
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
    def serialize(suite_items):
        return {
            'items': [SuiteSerializer.serialize_item(i) for i in suite_items],
        }

    @staticmethod
    def serialize_item(item):
        data = {
            'type': item.type,
            'location': LocationSerializer.serialize(item.location),
        }
        if item.size:
            data['file_size'] = item.size
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
        return {
            'type': item.type,
            'location': LocationSerializer.serialize(item.location),
        }


class ReportSerializer:

    @staticmethod
    def serialize(report):
        return {
            'items': [ReportSerializer.serialize_item(i) for i in report.items],
            'pending_at': report.pending_at.strftime(Serializer.date_format),
            'started_at': report.started_at.strftime(Serializer.date_format),
            'finished_at': report.finished_at.strftime(Serializer.date_format),
        }

    @staticmethod
    def serialize_item(item):
        data = {
            'type': str(item.type),
            'location': LocationSerializer.serialize(item.location),
            'status': item.status,
        }
        if item.started_at:
            data['started_at'] = item.started_at.strftime(Serializer.date_format)
        if item.finished_at:
            data['finished_at'] = item.finished_at.strftime(Serializer.date_format)
        if item.error:
            data['error'] = {
                'type': Serializer.truncate(item.error.type, 1024),
                'message': Serializer.truncate(item.error.message, 1024),
            }
        return data


class ScheduleSerializer:
    from testandconquer.model import ScheduleItem

    @staticmethod
    def deserialize(data):
        items = [ScheduleItem(item['file']) for item in data['items']]
        logger.info('received schedule with %s items', len(items))
        return Schedule(items)


class LocationSerializer:
    @staticmethod
    def serialize(item):
        data = {
            'file': Serializer.truncate(item.file, 1024),
        }
        if item.func:
            data['func'] = Serializer.truncate(item.func, 1024)
        if item.module:
            data['module'] = Serializer.truncate(item.module, 1024)
        if item.cls:
            data['class'] = Serializer.truncate(item.cls, 1024)
        if item.line:
            data['line'] = item.line
        return data

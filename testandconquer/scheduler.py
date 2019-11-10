import asyncio

from contextlib import suppress

from testandconquer import logger
from testandconquer.client import Client
from testandconquer.model import Schedule, ScheduleBatch, ScheduleItem


class Scheduler:
    def __init__(self, settings, worker_id):
        self.settings = settings
        self.config = ConfigSerializer.serialize(self.settings, worker_id)
        logger.debug('generated config: %s', self.config)

    async def start(self, suite_items):
        self.client = Client(self.settings)
        self.task = asyncio.ensure_future(self._report_task())

        logger.debug('initialising suite with %s item(s)', len(suite_items))
        suite_data = SuiteSerializer.serialize(self.config, suite_items)
        schedule_data = await self._make_http_call(self.client.post, '/schedules', suite_data)
        self.run_id = schedule_data['run_id']
        self.job_id = schedule_data['job_id']
        self.schedule_queue = asyncio.Queue()
        self.__parse_schedule(schedule_data)
        return await self.schedule_queue.get()

    async def next(self, report_items):
        logger.debug('submitting report with %s item(s)', len(report_items))
        self.report_queue.put_nowait(report_items)
        return await self.schedule_queue.get()

    async def stop(self):
        await self.report_queue.join()
        self.task.cancel()
        with suppress(asyncio.CancelledError):
            await self.task

    async def _report_task(self):
        logger.debug('initialising report task')
        self.report_queue = asyncio.Queue()
        while True:
            try:
                report_items = await self.report_queue.get()
                logger.debug('sending %s completed item(s)', len(report_items))
                completed_data = ReportSerializer.serialize(self.run_id, self.job_id, report_items)
                schedule_data = await self._make_http_call(self.client.put, '/schedules', completed_data)
                self.__parse_schedule(schedule_data)
                self.report_queue.task_done()
            except asyncio.CancelledError:
                break

    def __parse_schedule(self, data):
        schedule_batches = []
        for batch in data['batches']:
            schedule_batches.append(ScheduleBatch([ScheduleItem(item['file']) for item in batch['items']]))
        logger.debug('received schedule with %s batches', len(schedule_batches))
        self.schedule_queue.put_nowait(Schedule(schedule_batches))

    def _make_http_call(self, func, path, data):
        return asyncio.get_event_loop().run_in_executor(None, func, path, data)


class Serializer:

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
                'capabilities': [c.value for c in settings.client_capabilities],
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
            'file': Serializer.truncate(item.location.file, 1024),
            'func': Serializer.truncate(item.location.func, 1024),
            'line': item.location.line,
        }
        if item.location.module:
            data['module'] = Serializer.truncate(item.location.module, 1024)
        if item.location.cls:
            data['class'] = Serializer.truncate(item.location.cls, 1024)
        return data


class ReportSerializer:

    date_format = '%Y-%m-%dT%H:%M:%S.000Z'

    @staticmethod
    def serialize(run_id, job_id, report_items):
        return {
            'run_id': run_id,
            'job_id': job_id,
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
        }
        if item.started_at:
            data['started_at'] = item.started_at.strftime(ReportSerializer.date_format)
        if item.finished_at:
            data['finished_at'] = item.finished_at.strftime(ReportSerializer.date_format)
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

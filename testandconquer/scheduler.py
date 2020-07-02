import asyncio
from contextlib import suppress

from testandconquer import logger
from testandconquer.client import MessageType
from testandconquer.serializer import Serializer
from testandconquer.util import system_exit


class Scheduler:
    def __init__(self, settings, client, suite_items, worker_id, serializer=Serializer):
        self.settings = settings
        self.client = client
        self.suite_items = suite_items
        self.worker_id = worker_id
        self.serializer = serializer

        self.more = True
        self.schedule_queue = asyncio.Queue()
        self.report_queue = asyncio.Queue()
        self.task = asyncio.ensure_future(self._report_task())
        client.subscribe(self)

    async def next(self):
        return await self.schedule_queue.get()

    async def report(self, schedule_id, report):
        logger.info('acking schedule %s', schedule_id)
        await self.client.send(MessageType.Ack, {'schedule_id': schedule_id, 'status': 'success'})
        logger.info('submitting report with %s item(s)', len(report.items))
        await self.report_queue.put(report)

    async def stop(self):
        await self.report_queue.join()
        self.task.cancel()
        with suppress(asyncio.CancelledError):
            await self.task

    async def on_server_message(self, message_type, payload):
        if message_type == MessageType.Config.value:
            config_data = self.serializer.serialize_config(self.settings, self.worker_id)
            logger.info('generated config: %s', config_data)
            await self.client.send(MessageType.Config, config_data)
        elif message_type == MessageType.Suite.value:
            suite_data = self.serializer.serialize_suite(self.suite_items)
            logger.info('initialising suite with %s item(s)', len(self.suite_items))
            await self.client.send(MessageType.Suite, suite_data)
        elif message_type == MessageType.Schedules.value:
            for schedule_data in payload:
                schedule = self.serializer.deserialize_schedule(schedule_data)
                logger.info('received schedule with %s item(s)', len(schedule.items))
                await self.schedule_queue.put(schedule)
        elif message_type == MessageType.Done.value:
            self.more = False
            await self.schedule_queue.put(None)  # so we unblock 'next'
        elif message_type == MessageType.Error.value:
            system_exit(payload['title'], payload['body'], payload['meta'])

    async def _report_task(self):
        logger.info('initialising report task')
        while True:
            try:
                report = await self.report_queue.get()
                logger.info('sending %s completed item(s)', len(report.items))
                report_data = self.serializer.serialize_report(report)
                await self.client.send(MessageType.Report, report_data)
                self.report_queue.task_done()
            except asyncio.CancelledError:
                break

    @property
    def done(self):
        return self.schedule_queue.empty and not self.more

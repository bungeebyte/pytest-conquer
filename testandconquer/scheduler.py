import asyncio
from threading import Event, Thread

from testandconquer import logger
from testandconquer.client import Client, MessageType
from testandconquer.serializer import Serializer
from testandconquer.util import system_exit, cancel_tasks_safely
from testandconquer.vendor.janus import Queue


class Scheduler(Thread):
    def __init__(self, settings):
        Thread.__init__(self)

        self.ready = Event()
        self.settings = settings
        self.suite_items = None
        self.client = Client(settings)
        self.serializer = Serializer()

        self.suite_items_requested = False
        self.stopping = False
        self.more = True

    def run(self):
        logger.info('starting up')
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.client_task = self.client.start()
            self.submit_task = asyncio.ensure_future(self._submit_task())
            self.receive_task = asyncio.ensure_future(self._receive_task())
            self.loop.run_forever()
        finally:
            logger.info('closing event loop')
            self.loop.close()
        logger.info('thread finished')

    def prepare(self, suite_items):
        self.suite_items = suite_items  # thread-safe, in case you were wondering

        # try to send the suite
        self._send_suite()

        # wait for thread to be fully started
        logger.info('waiting for thread to be ready')
        self.ready.wait()

    def next(self):
        return self.schedule_queue.sync_q.get()

    def report(self, report):
        self.report_queue.sync_q.put(report)

    def stop(self):
        logger.info('shutting down')

        # schedule task to gracefully stop everything
        asyncio.run_coroutine_threadsafe(self._stop_task(), loop=self.loop)

        # wait till everything is shutdown
        logger.info('waiting for thread to finish')
        self.join()

    async def _submit_task(self):
        self.report_queue = Queue()

        try:
            while True:
                report = await self.report_queue.async_q.get()

                # first, send ack
                logger.info('acking schedule %s', report.schedule_id)
                self.client.send(MessageType.Ack, {'schedule_id': report.schedule_id, 'status': 'success'})

                # then, send full report
                logger.info('sending %s completed item(s)', len(report.items))
                report_data = self.serializer.serialize_report(report)
                self.client.send(MessageType.Report, report_data)
        except asyncio.CancelledError:
            logger.info('submitter cancelled')
            pass  # we are shutting down

    async def _receive_task(self):
        self.schedule_queue = Queue()
        self.ready.set()

        try:
            while True:
                message_type, payload = await self.client.incoming.async_q.get()
                if message_type == MessageType.Envs.value:
                    self.settings.init_from_mapping(payload)
                    self.client.send(MessageType.Envs, self.settings.args['system_provider'])
                elif message_type == MessageType.Config.value:
                    config_data = self.serializer.serialize_config(self.settings)
                    logger.info('generated config: %s', config_data)
                    self.client.send(MessageType.Config, config_data)
                elif message_type == MessageType.Suite.value:
                    self.suite_items_requested = True
                    self._send_suite()
                elif message_type == MessageType.Schedules.value:
                    for schedule_data in payload:
                        schedule = self.serializer.deserialize_schedule(schedule_data)
                        logger.info('received schedule with %s item(s)', len(schedule.items))
                        await self.schedule_queue.async_q.put(schedule)
                elif message_type == MessageType.Done.value:
                    self.more = False
                    await self.schedule_queue.async_q.put(None)  # so we unblock 'next'
                elif message_type == MessageType.Error.value:
                    system_exit(payload['title'], payload['body'], payload['meta'])
        except asyncio.CancelledError:
            logger.info('receiver cancelled')
            pass  # we are shutting down

    def _send_suite(self):
        if self.suite_items and self.suite_items_requested:
            suite_data = self.serializer.serialize_suite(self.suite_items)
            logger.info('initialising suite with %s item(s)', len(self.suite_items))
            self.client.send(MessageType.Suite, suite_data)

    async def _stop_task(self):
        # we have to wait until all reports have been enqueued
        reports_left = self.report_queue.async_q.qsize()
        if reports_left > 0:
            logger.info('waiting for last %s reports to send', reports_left)
            await self.report_queue.async_q.join()

        # now we can safely stop the client
        await self.client.stop()

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        logger.info('cancelling remaining %s tasks', len(tasks))
        await cancel_tasks_safely(tasks)

        # now the loop can be safely stopped
        logger.info('stopping event loop')
        self.loop.stop()

    @property
    def done(self):
        return getattr(self, 'schedule_queue').sync_q.empty() and not self.more

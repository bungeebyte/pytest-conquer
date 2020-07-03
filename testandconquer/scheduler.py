from queue import Queue, Empty
from threading import Thread

from testandconquer import logger
from testandconquer.client import Client, MessageType
from testandconquer.serializer import Serializer
from testandconquer.util import system_exit


class Scheduler(Thread):
    def __init__(self, settings, suite_items, client=None, serializer=None):
        Thread.__init__(self)

        self.settings = settings
        self.suite_items = suite_items
        self.client = client or Client(settings)
        self.client.subscribe(self.settings)
        self.client.subscribe(self)
        self.serializer = serializer or Serializer

        self.stopping = False
        self.more = True
        self.schedule_queue = Queue()
        self.report_queue = Queue()

    def run(self):
        self.client.start()
        self._report_loop()

    def next(self):
        return self.schedule_queue.get()

    def report(self, report):
        self.report_queue.put(report)

    def stop(self):
        # quiescent the scheduler
        self.stopping = True

        # we have to wait until all reports have been sent
        self.report_queue.join()

        # stop client
        self.client.stop()

    def on_server_message(self, message_type, payload):
        if message_type == MessageType.Config.value:
            config_data = self.serializer.serialize_config(self.settings)
            logger.info('generated config: %s', config_data)
            self.client.send(MessageType.Config, config_data)
        elif message_type == MessageType.Suite.value:
            suite_data = self.serializer.serialize_suite(self.suite_items)
            logger.info('initialising suite with %s item(s)', len(self.suite_items))
            self.client.send(MessageType.Suite, suite_data)
        elif message_type == MessageType.Schedules.value:
            for schedule_data in payload:
                schedule = self.serializer.deserialize_schedule(schedule_data)
                logger.info('received schedule with %s item(s)', len(schedule.items))
                self.schedule_queue.put(schedule)
        elif message_type == MessageType.Done.value:
            self.more = False
            self.schedule_queue.put(None)  # so we unblock 'next'
        elif message_type == MessageType.Error.value:
            system_exit(payload['title'], payload['body'], payload['meta'])

    def _report_loop(self):
        while not self.stopping or not self.report_queue.empty():
            try:
                print('wait for report')
                report = self.report_queue.get(timeout=1)
                print(report)

                # first, send ack
                logger.info('acking schedule %s', report.schedule_id)
                self.client.send(MessageType.Ack, {'schedule_id': report.schedule_id, 'status': 'success'})

                # then, send full report
                logger.info('sending %s completed item(s)', len(report.items))
                report_data = self.serializer.serialize_report(report)
                self.client.send(MessageType.Report, report_data)

                self.report_queue.task_done()
            except Empty:
                return

    @property
    def done(self):
        return self.schedule_queue.empty() and not self.more

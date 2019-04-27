import multiprocessing
from _pytest.terminal import TerminalReporter


class ParallelTerminalReporter(TerminalReporter):

    def __init__(self, builtin_reporter, manager):
        TerminalReporter.__init__(self, builtin_reporter.config)
        self.report_log = manager.list()
        self.report_log_lock = manager.Lock()

    def pytest_runtest_logreport(self, report):
        reports_to_log = []
        with self.report_log_lock:
            if self.is_child_process:
                self.report_log.append(report)
            else:
                reports_to_log.extend(self.report_log)
                self.report_log[:] = []

        # we're calling the terminal reporter outside of the lock
        # to block as short as possible
        for rep in reports_to_log:
            TerminalReporter.pytest_runtest_logreport(self, rep)

    @property
    def is_child_process(self):
        return multiprocessing.current_process().name != 'MainProcess'

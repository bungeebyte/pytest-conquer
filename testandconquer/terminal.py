from _pytest.terminal import TerminalReporter


class ParallelTerminalReporter(TerminalReporter):

    def __init__(self, builtin_reporter, manager):
        TerminalReporter.__init__(self, builtin_reporter.config)
        self.report_log_lock = manager.Lock()
        self.report_log = manager.list()

    def pytest_runtest_logstart(self, nodeid, location):
        # this would otherwise print the test path twice
        pass

    def pytest_runtest_logreport(self, report):
        rep = report
        res = self.config.hook.pytest_report_teststatus(report=rep, config=self.config)
        cat, letter, word = res

        with self.report_log_lock:
            self.report_log.append(rep)

    def flush(self):
        with self.report_log_lock:
            for rep in self.report_log:
                TerminalReporter.pytest_runtest_logreport(self, rep)
            self.report_log[:] = []

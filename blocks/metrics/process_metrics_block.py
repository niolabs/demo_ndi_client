import psutil

from nio.block.base import Block
from nio.properties import ObjectProperty, IntProperty, \
    PropertyHolder, BoolProperty, VersionProperty
from nio.signal.base import Signal

RETRY_LIMIT = 3


class Menu(PropertyHolder):

    virtual_memory = BoolProperty(title='Virtual Memory', default=True)
    memory_percent = BoolProperty(title='Memory Percentage', default=True)
    cpu_percent = BoolProperty(title='CPU Percentage', default=True)
    num_ctx_switches = BoolProperty(
        title='Number of Context Switches', default=True)
    num_fds = BoolProperty(title='Number of File Descriptors', default=True)
    is_running = BoolProperty(title='Is Running?', default=True)

    children = BoolProperty(title='Children', default=False)
    threads = BoolProperty(title='Threads', default=False)
    cmd_line = BoolProperty(title='Command Line', default=False)


class NoPIDException(Exception):
    pass


class ProcessMetrics(Block):

    version = VersionProperty('0.1.0', min_version='0.1.0')
    menu = ObjectProperty(Menu, title='Menu', default=Menu())
    pid = IntProperty(title='PID', allow_none=False)

    def __init__(self):
        super().__init__()
        self._retry_count = 0

    def process_signals(self, signals):
        results = []
        for sig in signals:
            pid = self.pid(sig)
            stats = self._collect_stats(pid)
            if stats:
                results.append(Signal(stats))
        if results:
            self.notify_signals(results)

    def _collect_stats(self, pid):
        result = {'pid': pid}
        proc = psutil.Process(pid)

        try:
            if self.menu().cpu_percent():
                result['cpu_percentage'] = proc.cpu_percent()

            if self.menu().memory_percent():
                result['memory_percent'] = proc.memory_percent()

            if self.menu().virtual_memory():
                result['virtual_memory'] = proc.memory_info()[1]

            if self.menu().num_ctx_switches():
                result['num_ctx_switches'] = proc.num_ctx_switches()

            if self.menu().num_fds():
                result['num_fds'] = proc.num_fds()

            if self.menu().is_running():
                result['is_running'] = proc.is_running()

            if self.menu().children():
                result['children'] = proc.children()

            if self.menu().threads():
                result['threads'] = proc.threads()

            if self.menu().cmd_line():
                result['cmd_line'] = ' '.join(proc.cmdline())

        except Exception as e:
            self.logger.error(
                "While processing system metrics: {0}".format(str(e))
            )
            if self._retry_count < RETRY_LIMIT:
                self._retry_count += 1
                return self._collect_stats(pid)
            else:
                self.logger.error(
                    "System report failed {0} times, aborting...".format(
                        RETRY_LIMIT)
                )
                self._retry_count = 0
                return None
        else:
            self._retry_count = 0
            return result

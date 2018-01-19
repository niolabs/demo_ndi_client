import os
from threading import Event

from nio.block.terminals import DEFAULT_TERMINAL
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from nio.util.discovery import not_discoverable

from ..process_metrics_block import ProcessMetrics


@not_discoverable
class EventProcessMetrics(ProcessMetrics):

    def __init__(self, e):
        super().__init__()
        self._e = e

    def process_signals(self, signals):
        super().process_signals(signals)
        self._e.set()


class TestProcessMetricsBlock(NIOBlockTestCase):

    def setUp(self):
        super().setUp()
        self.expected = [
            'cpu_percentage',
            'virtual_memory',
            'num_ctx_switches',
            'memory_percent',
            'num_fds',
            'is_running',
            'pid'
        ]

    def test_generate_metrics(self):
        event = Event()
        blk = EventProcessMetrics(event)
        self.configure_block(blk, {
            'pid': "{{ $pid }}"
        })
        the_pid = os.getpid()
        blk.start()
        blk.process_signals([Signal({'pid': the_pid})])
        event.wait(1)
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertIsNotNone(self.last_notified)

        for k in self.last_notified[DEFAULT_TERMINAL][0].to_dict():
            for idx, f in enumerate(self.expected):
                if k.startswith(f):
                    break
                elif idx == len(self.expected)-1:
                    raise AssertionError("Unexpected report key '%s'" % k)

from threading import Event
from unittest.mock import patch

from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase
from nio.signal.base import Signal
from nio.util.discovery import not_discoverable

from ..host_specs_block import HostSpecs


@not_discoverable
class EventMetrics(HostSpecs):

    def __init__(self, e):
        super().__init__()
        self._e = e

    def process_signals(self, signals):
        super().process_signals(signals)
        self._e.set()


class TestHostSpecsBlock(NIOBlockTestCase):

    def setUp(self):
        super().setUp()
        self.expected = ['system']

    def test_generate_specs(self):
        event = Event()
        blk = EventMetrics(event)
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals([Signal()])
        event.wait(1)
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertTrue(self.last_notified)
        for k in self.last_notified[DEFAULT_TERMINAL][0].to_dict():
            for idx, f in enumerate(self.expected):
                if k.startswith(f):
                    break
                elif idx == len(self.expected)-1:
                    raise AssertionError("Unexpected report key '%s'" % k)

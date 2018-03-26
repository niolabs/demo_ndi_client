from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase
from nio.signal.base import Signal

from ..replicator_block import Replicator


class DummySignal(Signal):

    def __init__(self, val, list=[None]):
        super().__init__()
        self.val = val
        self.list = list


class TestReplicator(NIOBlockTestCase):

    def test_block(self):
        signals = [DummySignal("a banana!", [1, 2])]
        blk = Replicator()
        self.configure_block(blk, {'title': 'new_value',
                                   'list': '{{$list}}'})
        blk.start()
        blk.process_signals(signals)
        self.assertEqual(len(self.last_notified[DEFAULT_TERMINAL]), 2)
        self.assertTrue(
            self.last_notified[DEFAULT_TERMINAL][0].new_value in [1, 2])
        self.assertTrue(
            self.last_notified[DEFAULT_TERMINAL][1].new_value in [1, 2])

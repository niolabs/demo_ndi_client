from unittest.mock import MagicMock
from time import sleep

from nio import Signal, Block
from nio.util.discovery import not_discoverable
from nio.testing.block_test_case import NIOBlockTestCase

from ...triggers.safe import SafeTrigger


@not_discoverable
class SampleSafeBlock(SafeTrigger, Block):
    pass


def slow_signal_generator(n):
    """ Takes some time to generate a signal """
    sleep(0.3)
    return [Signal()]


class TestSafe(NIOBlockTestCase):

    def setUp(self):
        super().setUp()
        self.signals_out = 0

    def signals_notified(self, signals, output_id='default'):
        self.signals_out += len(signals)

    def test_safe_normal(self):
        """ Test that we can generate normally - 5 sigs/sec """
        safe = SampleSafeBlock()
        self.configure_block(safe, {
            'interval': {
                'seconds': 1
            },
            'max_count': 5
        })
        returns = [Signal()]
        safe.generate_signals = MagicMock(return_value=returns)

        # Give it enough time to complete two cycles - one right when the block
        # starts, the other after the first second has elapsed
        safe.start()
        sleep(1.5)
        safe.stop()

        self.assert_num_signals_notified(10)

    def test_safe_slow(self):
        """ Test that we still notify when we can't generate fast enough """
        safe = SampleSafeBlock()
        self.configure_block(safe, {
            'interval': {
                'seconds': 1
            },
            'max_count': 7,
            'log_level': 'DEBUG'
        })
        safe.generate_signals = slow_signal_generator
        safe.start()

        # After a little more than one second, we should have seen a
        # notification but not with every signal
        sleep(1.5)
        self.assertLess(self.signals_out, 7)
        self.signals_out = 0

        # One second later, should be the same story
        sleep(1)
        self.assertLess(self.signals_out, 7)

        safe.stop()

from unittest.mock import MagicMock
from time import sleep

from nio import Signal, Block
from nio.util.discovery import not_discoverable
from nio.testing.block_test_case import NIOBlockTestCase

from ...triggers.interval import IntervalTrigger


@not_discoverable
class SampleIntervalBlock(IntervalTrigger, Block):
    pass


class TestInterval(NIOBlockTestCase):

    def test_interval_default(self):
        """ Interval trigger notifies all signals
        when total signals is not specified.
        """
        interval = SampleIntervalBlock()
        self.configure_block(interval, {
            'interval': {
                'seconds': 1
            }
        })
        returns = [Signal(), Signal()]
        interval.generate_signals = MagicMock(return_value=returns)

        interval.start()
        # Give it enough time for two notifications
        # (one immediately, one after a second)
        sleep(1.5)
        interval.stop()

        self.assert_num_signals_notified(4)

    def test_total_signals(self):
        """ Total_signals limits notified signals to one
        despite enough time for two signals generated
        """
        interval = SampleIntervalBlock()
        self.configure_block(interval, {
            'interval': {
                'seconds': 1
            },
            'total_signals': 1
        })
        returns = [Signal()]
        interval.generate_signals = MagicMock(return_value=returns)

        interval.start()
        # Give it enough time for two notifications
        # but then the second one should not notify
        sleep(1.5)
        interval.stop()

        self.assert_num_signals_notified(1)

    def test_extra_generated_signals(self):
        """5 signals are notified despite 6 signals being generated
        due to multiple signals
        """
        interval = SampleIntervalBlock()
        self.configure_block(interval, {
            'interval': {
                'seconds': 0.1
            },
            'total_signals': 5
        })

        returns = [Signal(), Signal()]
        interval.generate_signals = MagicMock(return_value=returns)
        interval.start()
        sleep(0.5)
        interval.stop()

        # Although 6 signals are notified, the interval trigger only allows
        # 5 signals to be notified because total_signals is 5
        self.assert_num_signals_notified(5)

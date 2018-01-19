from time import time as _time
from unittest.mock import MagicMock, patch
from threading import Event

from nio.testing.block_test_case import NIOBlockTestCase
from nio.signal.base import Signal
from nio.util.discovery import not_discoverable

from ..sleep_block import Sleep


@not_discoverable
class SleepEvent(Sleep):

    def notify_signals(self, signals):
        super().notify_signals(signals)
        signals = [signals] if not isinstance(signals, list) else signals
        for signal in signals:
            if hasattr(signal, '_event'):
                signal._event.set()


class EventSignal(Signal):

    def __init__(self, attrs=None, event=None):
        super().__init__(attrs)
        self._event = event


class TestSleep(NIOBlockTestCase):

    def assert_persistence(self, blk, save_count):
        self.assertEqual(blk._persistence.save.call_count, save_count)
        self.assertEqual(blk._persistence.save.call_args[0][0],
                         {'_signals': blk._signals})

    def test_sleep_block(self):
        e = Event()
        blk = SleepEvent()
        self.configure_block(blk, {
            'log_level': 'DEBUG',
            'interval': {'seconds': 0.1}
        })
        blk.start()
        signals = [Signal({'name': 'signal1'}),
                   EventSignal({'name': 'signal2'}, e)]
        blk.process_signals(signals)
        # check that signals are not notified immediately
        # but are notified after a short wait
        self.assert_num_signals_notified(0)
        self.assertTrue(e.wait(2))
        self.assert_num_signals_notified(2)
        blk.stop()

    def test_interval_expression(self):
        """Test that intervals work with expression properties."""
        e = Event()
        blk = SleepEvent()
        self.configure_block(blk, {
            'log_level': 'DEBUG',
            'interval': '{{ datetime.timedelta(seconds=$interval) }}'
        })
        blk.start()
        signals = [Signal({'name': 'signal1', 'interval': 0.1}),
                   EventSignal({'name': 'signal2', 'interval': 0.1}, e)]
        blk.process_signals(signals)
        # check that signals are not notified immediately
        # but are notified after a short wait
        self.assert_num_signals_notified(0)
        self.assertTrue(e.wait(2))
        self.assert_num_signals_notified(2)
        blk.stop()

    def test_persist_save(self):
        blk = Sleep()
        self.configure_block(blk, {
            'log_level': 'DEBUG',
            'interval': {'seconds': 10}
        })
        blk._persistence.save = MagicMock()
        blk.start()
        signals_a = [Signal({'name': 'signal1'}),
                     Signal({'name': 'signal2'})]
        signals_b = [Signal({'name': 'signal3'}),
                     Signal({'name': 'signal4'})]
        # process some signals
        blk.process_signals(signals_a)
        # process some more signals
        blk.process_signals(signals_b)
        # stop the block and save persistence
        blk.stop()
        self.assert_persistence(blk, 1)
        # the block should have stopped before any signals were notified
        self.assert_num_signals_notified(0)
        # assert that two groups of signals were saved
        self.assertEqual(len(blk._signals), 2)
        # assert that each group has two signals
        self.assertEqual(len(blk._signals[0][1]), 2)
        self.assertEqual(len(blk._signals[1][1]), 2)
        # assert that the second set of signals has a later time than the first
        self.assertTrue(blk._signals[0][0] < blk._signals[1][0])

    def test_persist_load(self):
        ctime = _time()
        e = Event()
        blk = SleepEvent()
        signals1 = [Signal()]
        signals2 = [Signal(), EventSignal({}, e)]
        signals = [(ctime, signals1), (ctime + 1, signals2)]
        # Mock load _signals from persistence before configure call
        blk._signals = signals
        self.configure_block(blk, {
            'log_level': 'DEBUG',
            'interval': {'seconds': 1}
        })
        blk.start()
        # all signals load but only signals2 are put back into _signals
        self.assertEqual(blk._load_signals, signals)
        self.assertEqual(len(blk._signals), 1)
        self.assertEqual(len(blk._signals[0][1]), 2)
        self.assert_num_signals_notified(0)
        # wait for signals2 to be notified
        e.wait(2)
        self.assert_num_signals_notified(2)
        # then when the block stops, no more signals are stored
        blk.stop()
        self.assertEqual(len(blk._signals), 0)

    def test_persist_load_nothing(self):
        blk = SleepEvent()
        with patch('nio.modules.persistence.Persistence.load'):
            self.configure_block(blk, {
                'log_level': 'DEBUG',
                'interval': {'seconds': 10}
            })
        blk.start()
        self.assertEqual(blk._load_signals, [])
        blk.stop()

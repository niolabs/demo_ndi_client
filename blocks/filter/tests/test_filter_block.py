from unittest.mock import patch

from nio.testing.block_test_case import NIOBlockTestCase
from nio import Signal

from ..filter_block import Filter


class DummySignal(Signal):

    def __init__(self, val):
        super().__init__()
        self.val = val


class TestFilter(NIOBlockTestCase):

    def test_pass_all(self):
        signals = [1, 2, 3, 4]
        blk = Filter()
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(4, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')
        blk.stop()

    def test_pass_any(self):
        signals = [1, 2, 3, 4]
        blk = Filter()
        self.configure_block(blk, {'operator': 'ANY'})
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(0, blk, 'true')
        self.assert_num_signals_notified(4, blk, 'false')
        blk.stop()

    def test_filter_odd(self):
        signals = [
            DummySignal(1),
            DummySignal(2),
            DummySignal(3),
            DummySignal(4)
        ]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': '{{$val % 2 == 0}}'}
            ]
        })
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(2, blk, 'true')
        self.assert_num_signals_notified(2, blk, 'false')
        blk.stop()

    def test_access_signal_attrs(self):
        signals = [DummySignal(23)]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': '{{$val != 23}}'}
            ]
        })
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(0, blk, 'true')
        self.assert_num_signals_notified(1, blk, 'false')
        blk.stop()

    def test_bogus_expr(self):
        signals = [DummySignal(23)]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': '{{$vals != 23}}'}
            ]
        })
        blk.start()
        with patch.object(blk, "logger") as patched_logger:
            # 'vals' doesn't exist on the signal, so process_signals will error
            with self.assertRaises(AttributeError):
                blk.process_signals(signals)
            self.assertEqual(patched_logger.exception.call_count, 1)
        blk.stop()
        # should not output a signal at all and raise an exception
        self.assert_num_signals_notified(0, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')

    def test_bogus_expr2(self):
        signals = [DummySignal('anything')]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': ('{{datetime.timeskelta(2) >'
                          'datetime.timeskelta(1)}}')}
            ]
        })
        blk.start()
        with patch.object(blk, "logger") as patched_logger:
            # 'vals' doesn't exist on the signal, so process_signals will error
            with self.assertRaises(AttributeError):
                blk.process_signals(signals)
            self.assertEqual(patched_logger.exception.call_count, 1)
        # should not output a signal at all and raise an exception
        self.assert_num_signals_notified(0, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')
        blk.stop()

    def test_satisfy_any(self):
        signals = [
            DummySignal(23),
            DummySignal(52)
        ]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': '{{$val == 23}}'},
                {'expr': '{{$val == 52}}'}
            ],
            'operator': 'ANY'
        })
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(2, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')
        blk.stop()

    def test_satisfy_all(self):
        signals = [DummySignal(23), DummySignal(52)]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': '{{$val == 23}}'},
                {'expr': '{{$val == 52}}'}
            ],
            'operator': 'ALL'
        })
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(0, blk, 'true')
        self.assert_num_signals_notified(2, blk, 'false')
        blk.stop()

    def test_no_duplicates(self):
        signals = [DummySignal(23 * 52)]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': '{{$val % 23 == 0}}'},
                {'expr': '{{$val % 52 == 0}}'}
            ],
            'operator': 'ANY'
        })
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(1, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')
        blk.stop()

    def test_regex(self):
        signals = [DummySignal("foobar")]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': '{{re.match("foo", $val) is not None}}'}
            ]
        })
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(1, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')
        blk.stop()

    def test_math(self):
        signals = [DummySignal(0)]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': '{{$val == math.log(1)}}'}
            ]
        })
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(1, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')
        blk.stop()

    def test_regex2(self):
        signals = [DummySignal('anything')]
        blk = Filter()
        self.configure_block(blk, {
            'conditions': [
                {'expr': ('{{datetime.timedelta(2) >'
                          'datetime.timedelta(1)}}')}
            ]
        })
        blk.start()
        blk.process_signals(signals)
        self.assert_num_signals_notified(1, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')
        blk.stop()

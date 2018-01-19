from unittest.mock import patch
from nio.block.terminals import DEFAULT_TERMINAL
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from .test_state_base import StateSignal
from ..switch_block import Switch


class OtherSignal(Signal):

    def __init__(self, state):
        super().__init__()
        self.other = state


class TestSwitch(NIOBlockTestCase):

    def test_switch(self):
        blk = Switch()
        self.configure_block(blk, {
            'state_expr': '{{ $state }}',
            'initial_state': '{{ False }}',
            'group_by': None
        })
        blk.start()

        self.assertFalse(blk.get_state(None))

        # set state to True
        blk.process_signals([StateSignal('1')], input_id='setter')
        self.assertEqual(blk.get_state(None), '1')
        self.assertTrue(bool(blk.get_state(None)))
        self.assert_num_signals_notified(0, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')

        # send a true state + other signal
        blk.process_signals([StateSignal('2')], input_id='setter')
        blk.process_signals([OtherSignal('3')])
        self.assert_num_signals_notified(1, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')
        self.assertEqual(blk.get_state(None), '2')
        self.assertTrue(bool(blk.get_state(None)))
        self.assertEqual(self.last_notified['true'][0].other, '3')

        # signals pass through to false output when State is false
        blk.process_signals([StateSignal(False)], input_id='setter')
        blk.process_signals([OtherSignal('4')])
        self.assertFalse(bool(blk.get_state(None)))
        self.assert_num_signals_notified(1, blk, 'true')
        self.assert_num_signals_notified(1, blk, 'false')

        # signals still pass through to false output
        blk.process_signals([OtherSignal(n) for n in range(100)])
        self.assertEqual(blk.get_state(None), False)
        self.assert_num_signals_notified(1, blk, 'true')
        self.assert_num_signals_notified(101, blk, 'false')

        # set state to 1 and get notification signal.
        blk.process_signals([StateSignal('1')], input_id='setter')
        blk.process_signals([OtherSignal('5')])
        self.assert_num_signals_notified(2, blk, 'true')
        self.assert_num_signals_notified(101, blk, 'false')
        self.assertEqual(blk.get_state(None), '1')
        self.assertTrue(bool(blk.get_state(None)))
        self.assertEqual(self.last_notified['true'][1].other, '5')
        blk.stop()

    def test_getter_input(self):
        blk = Switch()
        self.configure_block(blk, {
            # No signals in 'getter' input are state setter signals
            'state_expr': '{{ $state }}',
            'initial_state': '{{ False }}',
            'group_by': None
        })
        blk.start()
        # initial state is False so signals pass through false output
        blk.process_signals([OtherSignal('3')], input_id='getter')
        self.assert_num_signals_notified(0, blk, 'true')
        self.assert_num_signals_notified(1, blk, 'false')
        # set state to True
        blk.process_signals([StateSignal('1')], input_id='setter')
        # pass signals through
        blk.process_signals([OtherSignal('3')], input_id='getter')
        self.assert_num_signals_notified(1, blk, 'true')
        self.assert_num_signals_notified(1, blk, 'false')
        # set state back to False
        blk.process_signals([StateSignal('')], input_id='setter')
        # signals pass through to false output
        blk.process_signals([OtherSignal('3')], input_id='getter')
        self.assert_num_signals_notified(1, blk, 'true')
        self.assert_num_signals_notified(2, blk, 'false')

    def test_setter_input(self):
        blk = Switch()
        self.configure_block(blk, {
            # No signals in 'getter' input are state setter signals
            'state_expr': '{{ $state }}',
            'initial_state': '{{ False }}',
            'group_by': None
        })
        blk.start()
        self.assertFalse(blk.get_state(None))
        # set state to True
        blk.process_signals([StateSignal('1')], input_id='setter')
        self.assertEqual(blk.get_state(None), '1')
        self.assertTrue(bool(blk.get_state(None)))
        # set state back to False
        blk.process_signals([StateSignal('')], input_id='setter')
        self.assertEqual(blk.get_state(None), '')
        self.assertFalse(bool(blk.get_state(None)))
        # no signals were notified
        self.assert_num_signals_notified(0, blk, 'true')
        self.assert_num_signals_notified(0, blk, 'false')

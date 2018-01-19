from unittest.mock import patch
from nio.block.terminals import DEFAULT_TERMINAL
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from .test_state_base import StateSignal
from ..append_state_block import AppendState


class OtherSignal(Signal):

    def __init__(self, state):
        super().__init__()
        self.other = state


class TestAppendState(NIOBlockTestCase):

    def test_append_state(self):
        blk = AppendState()
        self.configure_block(blk, {
            'initial_state': '{{False}}',
            "state_expr": "{{$state}}",
            'group_by': None,
            "state_name": "mstate"
        })
        blk.start()

        signals_notified = 0

        # set state
        blk.process_signals([StateSignal('1')], input_id='setter')
        self.assertEqual(blk.get_state(None), '1')
        self.assert_num_signals_notified(signals_notified, blk)

        # set state + other signal
        blk.process_signals([StateSignal('2')], input_id='setter')
        blk.process_signals([OtherSignal('3')])
        signals_notified += 1
        self.assert_num_signals_notified(signals_notified, blk)
        self.assertEqual(blk.get_state(None), '2')
        self.assertEqual(self.last_notified[DEFAULT_TERMINAL][0].mstate, '2')

        # Just sending other signals pass through and have mstates of '2'
        blk.process_signals([OtherSignal(n) for n in range(100)])
        signals_notified += 100
        self.assertEqual(blk.get_state(None), '2')
        self.assert_num_signals_notified(signals_notified, blk)
        self.assertEqual(
            len(self.last_notified[DEFAULT_TERMINAL]), signals_notified)
        [self.assertEqual(n.mstate, '2')
         for n in self.last_notified[DEFAULT_TERMINAL]]

        blk.stop()

    def test_getter_input(self):
        blk = AppendState()
        self.configure_block(blk, {
            # No signals in 'getter' input are state setter signals
            'state_expr': '{{ $state }}',
            'initial_state': '{{ False }}',
            'group_by': None,
            'state_name': 'mstate'
        })
        blk.start()
        # getter should get initial statue of False
        blk.process_signals([OtherSignal('3')], input_id='getter')
        self.assertEqual(self.last_notified[DEFAULT_TERMINAL][0].mstate, False)
        self.assert_num_signals_notified(1, blk)
        # set state to '1'
        blk.process_signals([StateSignal('1')], input_id='setter')
        # getter should get state of '1'
        blk.process_signals([OtherSignal('3')], input_id='getter')
        self.assertEqual(self.last_notified[DEFAULT_TERMINAL][1].mstate, '1')
        self.assert_num_signals_notified(2, blk)

    def test_setter_input(self):
        blk = AppendState()
        self.configure_block(blk, {
            # No signals in default input are state setter signals
            'initial_state': '{{ False }}',
            "state_expr": "{{ $state }}",
            'group_by': None,
            'state_name': "mstate"
        })
        blk.start()
        # set state
        blk.process_signals([StateSignal('1')], input_id='setter')
        self.assertEqual(blk.get_state(None), '1')
        # set state again
        blk.process_signals([StateSignal('2')], input_id='setter')
        self.assertEqual(blk.get_state(None), '2')
        # no signals were notified
        self.assert_num_signals_notified(0, blk)

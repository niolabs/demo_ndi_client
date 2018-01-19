from unittest.mock import patch, MagicMock
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from ..state_base import StateBase


class StateSignal(Signal):

    def __init__(self, state, group='null'):
        super().__init__()
        self.state = state
        self.group = group


class TestStateBase(NIOBlockTestCase):

    def test_saves_state(self):
        """ Tests that the block saves states properly """
        blk = StateBase()
        self.configure_block(blk, {
            'state_expr': '{{$state}}',
            'initial_state': '{{None}}',
            'group_by': '{{$group}}'
        })
        # Should start out with our default state
        # which is configured to be None for this block
        self.assertIsNone(blk.get_state('A'))
        self.assertIsNone(blk.get_state('B'))
        # Process a few groups, setting states along the way
        blk._process_state(StateSignal(1), 'A')
        blk._process_state(StateSignal(2), 'B')
        blk._process_state(StateSignal(3), 'A')
        blk._process_state(StateSignal(3), 'A')
        # Make sure the latest state is kept for each group
        self.assertEqual(3, blk.get_state('A'))
        self.assertEqual(2, blk.get_state('B'))

    def test_process_return(self):
        """ Tests that process_state returns the correct values """
        blk = StateBase()
        self.configure_block(blk, {
            'state_expr': '{{$state}}',
            'initial_state': '{{None}}',
            'group_by': '{{$group}}'
        })
        # Make sure the initial state change contains the previous state
        # and new states
        process_out = blk._process_state(StateSignal(1), 'A')
        self.assertIsNone(process_out[0])  # previous state
        self.assertEqual(1, process_out[1])  # new state
        # Make sure that the same state returns a None
        process_out = blk._process_state(StateSignal(1), 'A')
        self.assertIsNone(process_out)
        # A new group should get a new state change though
        process_out = blk._process_state(StateSignal(1), 'B')
        self.assertIsNone(process_out[0])  # previous state
        self.assertEqual(1, process_out[1])  # new state
        # And then one more change of group A
        process_out = blk._process_state(StateSignal(5), 'A')
        self.assertEqual(1, process_out[0])  # previous state
        self.assertEqual(5, process_out[1])  # new state

    def test_bad_expr(self):
        """ Tests that the block won't save a state it can't evaluate """
        blk = StateBase()
        self.configure_block(blk, {
            'state_expr': '{{$state + 1}}',
            'initial_state': '{{None}}',
            'group_by': '{{$group}}'
        })
        # Make sure we have the initial state,
        # then send a signal that won't evaluate properly
        # make sure that did NOT set the state and we still
        # retained the original state
        self.assertIsNone(blk.get_state('A'))
        blk._process_state(StateSignal('hello'), 'A')
        self.assertIsNone(blk.get_state('A'))

    def test_process_signals(self):
        """ Test that process signals properly calls process_group """
        blk = StateBase()
        self.configure_block(blk, {
            'state_expr': '{{$state}}',
            'initial_state': '{{None}}',
            'group_by': '{{$group}}'
        })
        blk._process_group = MagicMock()
        blk.start()
        blk.process_signals([
            Signal({'group': 'A', 'state': 1}),
            Signal({'group': 'B', 'state': 2}),
            Signal({'group': 'A', 'state': 3}),
            Signal({'group': 'C', 'state': 4})])
        self.assertEqual(blk._process_group.call_count, 3)
        blk.stop()

    def test_current_state_command(self):
        """ Test the current_state block command """
        blk = StateBase()
        self.configure_block(blk, {})
        blk.start()
        # Test when state is not defined for group
        from nio.modules.web.http import HTTPNotFound
        with self.assertRaises(HTTPNotFound):
            blk.current_state('A')
        # Now test some valid states
        process_out = blk._process_state(StateSignal(1), 'A')
        self.assertDictEqual(blk.current_state('A'),
                             {'group': 'A', 'state': 1})
        process_out = blk._process_state(StateSignal(2), 'A')
        self.assertDictEqual(blk.current_state('A'),
                             {'group': 'A', 'state': 2})
        process_out = blk._process_state(StateSignal(1), 'B')
        self.assertDictEqual(blk.current_state('B'),
                             {'group': 'B', 'state': 1})
        # And all states
        self.assertListEqual(
            sorted(blk.current_state(group=None), key=lambda k: k['group']),
            [{'group': 'A', 'state': 2}, {'group': 'B', 'state': 1}])
        blk.stop()

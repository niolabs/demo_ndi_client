import datetime

from nio.block.terminals import DEFAULT_TERMINAL
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase

from ..join_block import Join


class TestJoin(NIOBlockTestCase):

    def signals_notified(self, block, signals, output_id):
        """ Don't extend last notified signals.

        We want to REPLACE the last signals notified each time the block
        notifies signals rather than EXTEND the list. This is done because it
        matters whether multiple lists of signals are notified or not.
        """
        self.last_notified[output_id] = signals

    def test_join(self):
        signals = [{'flavor': 'cherry', 'size': 'S'},
                   {'flavor': 'cherry', 'size': 'M'},
                   {'flavor': 'cherry', 'size': 'L'},
                   {'flavor': 'banana', 'size': 'S'},
                   {'flavor': 'apple', 'size': 'S'}]
        blk = Join()
        config = {
            "key": "{{$flavor}}",
            "value": "{{$size}}",
        }
        self.configure_block(blk, config)
        blk.start()
        blk.process_signals([Signal(s) for s in signals])
        self.assert_num_signals_notified(1, blk)
        self.assertEqual(
            ['S', 'M', 'L'], self.last_notified[DEFAULT_TERMINAL][0].cherry)
        self.assertEqual(['S'], self.last_notified[DEFAULT_TERMINAL][0].banana)
        self.assertEqual(['S'], self.last_notified[DEFAULT_TERMINAL][0].apple)
        blk.stop()

    def test_defaults(self):
        signals = [{'key': 'cherry', 'value': 'S'},
                   {'key': 'cherry', 'value': 'M'},
                   {'key': 'cherry', 'value': 'L'},
                   {'key': 'banana', 'value': 'S'},
                   {'key': 'apple', 'value': 'S'}]
        blk = Join()
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals([Signal(s) for s in signals])
        self.assert_num_signals_notified(1, blk)
        self.assertEqual(self.last_notified[DEFAULT_TERMINAL][0].to_dict(), {
            "apple": ['S'],
            "banana": ['S'],
            "cherry": ['S', 'M', 'L'],
            "group": None,
        })

    def test_defaults_with_enrich_signals(self):
        signals = [{'key': 'cherry', 'value': 'S'},
                   {'key': 'cherry', 'value': 'M'},
                   {'key': 'cherry', 'value': 'L'},
                   {'key': 'banana', 'value': 'S'},
                   {'key': 'apple', 'value': 'S'}]
        blk = Join()
        self.configure_block(blk, {
            "enrich": {"exclude_existing": False}
        })
        blk.start()
        blk.process_signals([Signal(s) for s in signals])
        self.assert_num_signals_notified(1, blk)
        self.assertEqual(self.last_notified[DEFAULT_TERMINAL][0].to_dict(), {
            "apple": ['S'],
            "banana": ['S'],
            "cherry": ['S', 'M', 'L'],
            "group": None,
            "key": "apple",
            "value": "S",
        })

    def test_one_value(self):
        signals = [{'key': 'cherry', 'value': 'S'},
                   {'key': 'cherry', 'value': 'M'},
                   {'key': 'cherry', 'value': 'L'},
                   {'key': 'banana', 'value': 'S'},
                   {'key': 'apple', 'value': 'S'}]
        blk = Join()
        config = {
            'one_value': True
        }
        self.configure_block(blk, config)
        blk.start()
        blk.process_signals([Signal(s) for s in signals])
        self.assert_num_signals_notified(1, blk)
        self.assertEqual('L', self.last_notified[DEFAULT_TERMINAL][0].cherry)
        self.assertEqual('S', self.last_notified[DEFAULT_TERMINAL][0].banana)
        self.assertEqual('S', self.last_notified[DEFAULT_TERMINAL][0].apple)

        # Make sure the bad one didn't make its way into the output signal
        self.assertFalse(
            hasattr(self.last_notified[DEFAULT_TERMINAL][0], 'flavor'))
        blk.stop()

    def test_grouping(self):
        signals = [{'group': 'fruit', 'key': 'cherry', 'value': 'S'},
                   {'group': 'fruit', 'key': 'cherry', 'value': 'M'},
                   {'group': 'fruit', 'key': 'cherry', 'value': 'L'},
                   {'group': 'pie', 'key': 'banana', 'value': 'S'},
                   {'group': 'pie', 'key': 'cherry', 'value': 'M'},
                   {'group': 'pie', 'key': 'cherry', 'value': 'L'},
                   {'group': 'fruit', 'key': 'banana', 'value': 'S'}]
        blk = Join()
        config = {
            'group_attr': 'my_group',
            'group_by': '{{$group}}',
            'log_level': 'DEBUG'
        }
        self.configure_block(blk, config)
        blk.process_signals([Signal(s) for s in signals])
        self.assert_num_signals_notified(2, blk)
        # Assert that only one list of signals was notified by checking that
        # the last notified had ALL of the signals
        self.assertEqual(len(self.last_notified[DEFAULT_TERMINAL]), 2)
        for sig_out in self.last_notified[DEFAULT_TERMINAL]:
            # Make sure the group got assigned to the right attr
            self.assertIn(sig_out.my_group, ['fruit', 'pie'])

            # Assert the right values went to the right groups
            if sig_out.my_group == 'fruit':
                self.assertEqual(len(sig_out.cherry), 3)
                self.assertEqual(len(sig_out.banana), 1)
            elif sig_out.my_group == 'pie':
                self.assertEqual(len(sig_out.cherry), 2)
                self.assertEqual(len(sig_out.banana), 1)

    def test_non_string_attributes(self):
        now = datetime.datetime.utcnow()
        signals = [{'name': 123, 'value': 456},
                   {'name': 'str', 'value': 'string'},
                   {'name': {}, 'value': {}},
                   {'name': "None", 'value': None},
                   {'name': now, 'value': now},
                   ]
        blk = Join()
        self.configure_block(blk, {
            "key": "{{ $name }}",
            "value": "{{ $value }}",
            "one_value": True
        })
        blk.start()
        blk.process_signals([Signal(s) for s in signals])
        self.assert_num_signals_notified(1, blk)
        self.assertDictEqual(self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
                             {
                                 "group": None,
                                 "123": 456,
                                 "str": "string",
                                 "{}": {},
                                 "None": None,
                                 str(now): now
                             })
        blk.stop()

from nio.block.terminals import DEFAULT_TERMINAL
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from ..attribute_selector_block import AttributeSelector


class TestExample(NIOBlockTestCase):

    def test_blacklist_attributes(self):
        """The 'hello' signal attribute will get blacklisted"""
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'BLACKLIST',
                                   'attributes': ['hello']})
        blk.start()
        blk.process_signals([Signal({'hello': 'n.io', 'goodbye': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        # should have blacklisted just hello
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {'goodbye': 'n.io'})

    def test_whitelist_attributes(self):
        """'hello' attribute passes through the block unmodified."""
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'WHITELIST',
                                   'attributes': ['hello']})
        blk.start()
        blk.process_signals([Signal({'hello': 'n.io', 'goodbye': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {'hello': 'n.io'})

    def test_no_attributes_specified_blacklist(self):
        """if no attributes are specified with blacklist behavior, expect
        original signal
        """
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'BLACKLIST',
                                   'attributes': []})
        blk.start()
        blk.process_signals([Signal({'hello': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {'hello': 'n.io'})

    def test_no_attributes_specified_whitelist(self):
        """if no attributes are specified with whitelist behavior, expect
        blank signal
        """
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'WHITELIST',
                                   'attributes': []})
        blk.start()
        blk.process_signals([Signal({'hello': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {})

    def test_hidden_attributes_blacklist(self):
        """make sure hidden attributes also work, blacklist"""
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'BLACKLIST',
                                   'attributes': ['_hello']})
        blk.start()
        blk.process_signals([Signal({'_hello': 'n.io', 'goodbye': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        # should have blacklisted the one incoming signal attribute
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(
                include_hidden=True),
            {'goodbye': 'n.io'}
        )

    def test_hidden_attributes_whitelist(self):
        """make sure hidden attributes also work, whitelist"""
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'WHITELIST',
                                   'attributes': ['_hello']})
        blk.start()
        blk.process_signals([Signal({'_hello': 'n.io', 'goodbye': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        # should have blacklisted the one incoming signal attribute
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(
                include_hidden=True),
            {'_hello': 'n.io'}
        )

    def test_extra_attributes_blacklist(self):
        """specified attributes that aren't in the signal should result in the
        original signal
        """
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'BLACKLIST',
                                   'attributes': ['test']})
        blk.start()
        blk.process_signals([Signal({'goodbye': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        # should have blacklisted the one incoming signal attribute
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {'goodbye': 'n.io'})

    def test_extra_attributes_whitelist(self):
        """specified attributes that aren't in the signal should result in the
        original signal
        """
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'WHITELIST',
                                   'attributes': ['test']})
        blk.start()
        blk.process_signals([Signal({'goodbye': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        # should have blacklisted the one incoming signal attribute
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {})

    def test_extra_attributes_multiple_whitelist(self):
        """specified attributes that aren't in the signal should result in
        the original signal
        """
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'WHITELIST',
                                   'attributes': ['test', 'yo']})
        blk.start()
        blk.process_signals([Signal({'test': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        # should have blacklisted the one incoming signal attribute
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {'test': 'n.io'})

    def test_extra_attributes_multiple_blacklist(self):
        """specified attributes that aren't in the signal should result in
        the original signal
        """
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'BLACKLIST',
                                   'attributes': ['test', 'yo']})
        blk.start()
        blk.process_signals([Signal({'goodbye': 'n.io'})])
        blk.stop()
        self.assert_num_signals_notified(1)
        # should have blacklisted the one incoming signal attribute
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {'goodbye': 'n.io'})

    def test_blacklist_dynamic_attributes(self):
        """The 'hello' signal attribute will get blacklisted"""
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'BLACKLIST',
                                   'attributes': '{{ $attrs }}'})
        blk.start()
        blk.process_signals([Signal({
            'attrs': ['discard', 'these', 'attrs'],
            'keep': 'happy',
            'discard': 'sad',
        })])
        blk.stop()
        self.assert_num_signals_notified(1)
        # should have blacklisted just hello
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {'keep': 'happy'})

    def test_whitelist_dynamic_attributes(self):
        """'hello' attribute passes through the block unmodified."""
        blk = AttributeSelector()
        self.configure_block(blk, {'mode': 'WHITELIST',
                                   'attributes': '{{ $attrs }}'})
        blk.start()
        blk.process_signals([Signal({
            'attrs': ['keep', 'these'],
            'keep': 'happy',
            'discard': 'sad',
        })])
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {'keep': 'happy'})

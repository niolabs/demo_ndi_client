from unittest import skip
from nio.block.terminals import DEFAULT_TERMINAL
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from ..modifier_block import Modifier


class DummySignal(Signal):

    def __init__(self, val):
        super().__init__()
        self.val = val


class TestModifier(NIOBlockTestCase):

    def test_pass(self):
        """Signals pass through unmodified when no fields are configured"""
        signals = [DummySignal('a banana!')]
        attrs = signals[0].__dict__
        blk = Modifier()
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals(signals)
        blk.stop()
        self.assertDictEqual(
            attrs, self.last_notified[DEFAULT_TERMINAL][0].__dict__)

    def test_add_field(self):
        """Signal get new attributes from configured fields"""
        signals = [DummySignal('a banana!')]
        blk = Modifier()
        config = {
            "fields": [{
                "title": "greeting",
                "formula": "I am {{ $val }}"
            }]
        }
        self.configure_block(blk, config)
        blk.start()
        blk.process_signals(signals)
        blk.stop()
        sig = self.last_notified[DEFAULT_TERMINAL][0]
        self.assertTrue(hasattr(sig, 'greeting'))
        self.assertTrue(hasattr(sig, 'val'))
        self.assertEqual(sig.greeting, 'I am a banana!')

    def test_exclude(self):
        """Signal only have new attributes when exclude is True"""
        signals = [DummySignal('gone...')]
        blk = Modifier()
        config = {
            "exclude": True,
            "fields": [{
                "title": "greeting",
                "formula": "I am {{ $val }}"
            }]
        }
        self.configure_block(blk, config)
        blk.start()
        blk.process_signals(signals)
        blk.stop()
        sig = self.last_notified[DEFAULT_TERMINAL][0]
        self.assertTrue(hasattr(sig, 'greeting'))
        self.assertFalse(hasattr(sig, 'val'))
        self.assertEqual(sig.greeting, 'I am gone...')

    def test_invalid_field_expression(self):
        """Signal is never notified if a field expression fails"""
        signals = [Signal()]
        blk = Modifier()
        self.configure_block(blk, {
            "exclude": True,
            "fields": [{
                "title": "greeting",
                "formula": "I am {{ dict('bad') }}"
            }]
        })
        blk.start()
        with self.assertRaises(Exception):
            blk.process_signals(signals)
        blk.stop()
        self.assertFalse(self.last_notified)

    def test_invalid_title_expression(self):
        """Signal is never notified if a title expression fails"""
        signals = [Signal()]
        blk = Modifier()
        self.configure_block(blk, {
            "exclude": True,
            "fields": [{
                "title": "This title will {{ fail }}",
                "formula": "I am sad"
            }]
        })
        blk.start()
        with self.assertRaises(Exception):
            blk.process_signals(signals)
        blk.stop()
        self.assertFalse(self.last_notified)

    def test_list_of_bad_signals(self):
        """No signals are notified if one of them fails"""
        signals = [DummySignal(""), Signal()]
        blk = Modifier()
        self.configure_block(blk, {
            "exclude": True,
            "fields": [{
                "title": "{{ $val }}",
                "formula": "Title is bad. You won't see me."
            }]
        })
        blk.start()
        with self.assertRaises(Exception):
            blk.process_signals(signals)
        blk.stop()
        self.assertFalse(self.last_notified)

    @skip("TODO: Empty titles actually are allowed right now but shouldn't be")
    def test_empty_title(self):
        """Empty titles are not allowed"""
        signals = [DummySignal("")]
        blk = Modifier()
        self.configure_block(blk, {
            "exclude": True,
            "fields": [{
                "title": "{{ $val }}",
                "formula": "Title is empty."
            }]
        })
        blk.start()
        blk.process_signals(signals)
        with self.assertRaises(Exception):
            blk.process_signals(signals)
        blk.stop()
        self.assertFalse(self.last_notified)

    def test_none_title(self):
        """None titles are not allowed"""
        signals = [DummySignal("")]
        blk = Modifier()
        self.configure_block(blk, {
            "exclude": True,
            "fields": [{
                "title": "{{ None }}",
                "formula": "Title is empty."
            }]
        })
        blk.start()
        with self.assertRaises(Exception):
            blk.process_signals(signals)
        blk.stop()
        self.assertFalse(self.last_notified)

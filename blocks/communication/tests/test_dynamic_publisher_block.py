import pickle
from base64 import b64encode
from collections import defaultdict
from unittest.mock import patch, Mock
from threading import Event

from nio import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from nio.util.discovery import not_discoverable

from ..dynamic_publisher import DynamicPublisher


class TestDynamicPublisher(NIOBlockTestCase):

    @patch(DynamicPublisher.__module__ + '.Publisher')
    def test_creating_a_publisher(self, pub):
        publisher = DynamicPublisher()
        topic = "topic.{{ $sig }}"

        self.configure_block(publisher, {"topic": topic})
        publisher.start()

        self.assertEqual(pub.call_count, 0)

        signals = [Signal(dict(sig="foo"))]
        publisher.process_signals(signals)

        pub.assert_called_once_with(topic="topic.foo")
        self.assertEqual(pub.return_value.open.call_count, 1)
        pub.return_value.send.assert_called_once_with(signals)

        publisher.stop()
        pub.return_value.close.assert_called_once_with()

    @patch(DynamicPublisher.__module__ + '.Publisher')
    def test_creating_multiple_publishers(self, pub):
        publisher = DynamicPublisher()
        topic = "topic.{{ $sig }}"

        self.configure_block(publisher, {"topic": topic})
        publisher.start()

        self.assertEqual(pub.call_count, 0)

        signals = [Signal(dict(sig="foo"))]
        publisher.process_signals(signals)

        pub.assert_called_once_with(topic="topic.foo")
        self.assertEqual(pub.return_value.open.call_count, 1)
        pub.return_value.send.assert_called_once_with(signals)

        pub.reset_mock()

        signals = [Signal(dict(sig="bar"))]
        publisher.process_signals(signals)

        pub.assert_called_once_with(topic="topic.bar")
        self.assertEqual(pub.return_value.open.call_count, 1)
        pub.return_value.send.assert_called_once_with(signals)

        publisher.stop()
        self.assertEqual(pub.return_value.close.call_count, 2)

    @patch(DynamicPublisher.__module__ + '.Publisher')
    def test_reusing_pubs(self, pub):
        publisher = DynamicPublisher()
        topic = "topic.{{ $sig }}"

        self.configure_block(publisher, {"topic": topic})
        publisher.start()

        self.assertEqual(pub.call_count, 0)

        signals = [Signal(dict(sig="foo", val=1))]
        publisher.process_signals(signals)

        pub.assert_called_once_with(topic="topic.foo")
        self.assertEqual(pub.return_value.open.call_count, 1)
        pub.return_value.send.assert_called_with(signals)

        signals = [Signal(dict(sig="foo", val=2))]
        publisher.process_signals(signals)

        self.assertEqual(pub.return_value.open.call_count, 1)
        pub.return_value.send.assert_called_with(signals)

    def test_partitioning(self):
        block = DynamicPublisher()

        self.configure_block(block, {"topic": "topic.{{ $sig }}"})
        block.start()

        signals = [
            Signal(dict(sig="foo", val=1)),
            Signal(dict(sig="bar", val=2)),
            Signal(dict(sig="baz", val=3)),
            Signal(dict(sig="foo", val=4)),
            Signal(dict(sig="bar", val=5)),
            Signal(dict(sig="foo", val=6)),
        ]

        publishers = defaultdict(Mock)
        with patch(DynamicPublisher.__module__ + '.Publisher', side_effect=lambda topic: publishers[topic]) as pub:
            block.process_signals(signals)

            self.assertEqual(pub.call_count, 3)
            pub.assert_any_call(topic="topic.foo")
            pub.assert_any_call(topic="topic.bar")
            pub.assert_any_call(topic="topic.baz")

        publishers.get("topic.foo").send.assert_called_once_with([
            Signal(dict(sig="foo", val=1)),
            Signal(dict(sig="foo", val=4)),
            Signal(dict(sig="foo", val=6)),
        ])

        publishers.get("topic.bar").send.assert_called_once_with([
            Signal(dict(sig="bar", val=2)),
            Signal(dict(sig="bar", val=5)),
        ])

        publishers.get("topic.baz").send.assert_called_once_with([
            Signal(dict(sig="baz", val=3)),
        ])

    @not_discoverable
    class EventDynamicPublisher(DynamicPublisher):

        def __init__(self, event):
            super().__init__()
            self._event = event

        def emit(self, reset=False):
            super().emit(reset)
            self._event.set()
            self._event.clear()

    @patch(DynamicPublisher.__module__ + '.Publisher')
    def test_closing(self, pub):
        event = Event()

        block = TestDynamicPublisher.EventDynamicPublisher(event)
        self.configure_block(block, dict(
            topic="topic.{{ $sig }}",
            ttl=dict(milliseconds=200),
        ))

        block.start()
        block.process_signals([Signal(dict(sig="foo"))])
        pub.assert_called_once_with(topic="topic.foo")
        self.assertEqual(pub.return_value.close.call_count, 0)

        event.wait(.3)

        self.assertEqual(pub.return_value.close.call_count, 1)

    @patch(DynamicPublisher.__module__ + '.Publisher')
    def test_local_dynamic_publisher(self, publisher):
        block = DynamicPublisher()
        topic = "topic.{{ $sig }}"

        self.configure_block(block, dict(
            topic=topic,
            is_local=True,
            local_identifier="test",
        ))

        block.start()
        self.assertEqual(publisher.call_count, 0)
        block.process_signals([Signal(dict(sig="foo"))])

        # should create the correct topic
        publisher.assert_called_once_with(topic="test.topic.foo")

        # should call send once
        self.assertEqual(publisher.return_value.send.call_count, 1)

        # should be the correct format
        self.assertEqual(
            [s.to_dict() for s in publisher.return_value.send.call_args[0][0]],
            [{"signals": b64encode(pickle.dumps([Signal(dict(sig="foo"))]))}])

    @patch(DynamicPublisher.__module__ + '.Publisher')
    def test_never_expiring(self, publisher):
        block = DynamicPublisher()
        topic = "topic.{{ $sig }}"

        self.configure_block(block, dict(
            topic=topic,
            ttl=dict(seconds=-1),
        ))

        block.start()
        self.assertEqual(publisher.call_count, 0)
        block.process_signals([Signal(dict(sig="foo"))])

        # should create the correct topic
        publisher.assert_called_once_with(topic="topic.foo")

        _, job = block._cache["topic.foo"]
        self.assertIsNone(job)

from base64 import b64encode
import pickle
from unittest.mock import patch, ANY

from nio import Signal
from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase

from ..local_publisher import LocalPublisher as Publisher
from ..local_subscriber import LocalSubscriber as Subscriber


class TestLocalPubSub(NIOBlockTestCase):

    def get_test_modules(self):
        return super().get_test_modules() | {'communication'}

    def test_publisher(self):
        publisher = Publisher()
        topic = "test_topic"
        instance_id = "id"

        with patch(Publisher.__module__ + '.NioPublisher') as communication:
            self.configure_block(
                publisher, {"topic": topic, "local_identifier": instance_id})
            communication.assert_called_once_with(
                topic="{}.{}".format(instance_id, topic))
            self.assertEqual(communication.return_value.open.call_count, 1)

            publisher.start()

            # Each list of processed signals publishes one new signal with the
            # pickled list of signals
            signals = [Signal({"a": "signal"})]
            publisher.process_signals(signals)
            self.assertEqual(1, communication.return_value.send.call_count)
            self.assertIsInstance(
                communication.return_value.send.call_args[0][0][0], Signal)
            self.assertEqual(
                [s.to_dict() for s in
                 communication.return_value.send.call_args[0][0]],
                [{"signals":
                  b64encode(pickle.dumps([Signal({"a": "signal"})]))}])

            publisher.stop()
            communication.return_value.close.assert_called_once_with()

    def test_subscriber(self):
        subscriber = Subscriber()
        topic = "test_topic"
        instance_id = "id"

        with patch(Subscriber.__module__ + '.NioSubscriber') as communication:
            self.configure_block(
                subscriber, {"topic": topic, "local_identifier": instance_id})
            communication.assert_called_once_with(
                ANY, topic="{}.{}".format(instance_id, topic))

            subscriber.start()
            self.assertEqual(communication.return_value.open.call_count, 1)

            # call the subscriber handler with a signal and then check that
            # signals are notified for decoded, unpickled result
            communication.call_args[0][0](
                [Signal({"signals":
                         b64encode(pickle.dumps([Signal({"a": "signal"})]))})])
            self.assert_num_signals_notified(1)
            self.assertEqual(
                [s.to_dict() for s in self.last_notified[DEFAULT_TERMINAL]],
                [{"a": "signal"}])

            subscriber.stop()
            communication.return_value.close.assert_called_once_with()

    def test_local_subscriber_nonlocal_publisher(self):
        """ Ensure the LocalSubscriber can handle Publisher signals """
        subscriber = Subscriber()

        with patch(Subscriber.__module__ + '.NioSubscriber') as communication:
            self.configure_block(
                subscriber, {"topic": "topic", "local_identifier": "test"})
            subscriber.start()

        # call the subscriber handler with a raw list of signals, not the
        # base64encoded signals that would come from the local publisher
        communication.call_args[0][0](
            [Signal({"key1": "val1"}), Signal({"key2": "val2"})])
        self.assert_num_signals_notified(2)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {"key1": "val1"}
        )
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][1].to_dict(),
            {"key2": "val2"}
        )
        subscriber.stop()


    def test_no_local_id(self):
        """ Make sure they can ignore the local id prefix if desired """
        subscriber = Subscriber()
        with patch(Subscriber.__module__ + '.NioSubscriber') as communication:
            self.configure_block(
                subscriber, {"topic": "topic", "local_identifier": ""})
            communication.assert_called_once_with(ANY, topic="topic")
        publisher = Publisher()
        with patch(Publisher.__module__ + '.NioPublisher') as communication:
            self.configure_block(
                publisher, {"topic": "topic", "local_identifier": ""})
            communication.assert_called_once_with(topic="topic")

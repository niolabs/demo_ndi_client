from unittest.mock import patch, ANY

from nio import Signal
from nio.testing.block_test_case import NIOBlockTestCase

from ..publisher import Publisher as Publisher
from ..subscriber import Subscriber as Subscriber


class TestPubSub(NIOBlockTestCase):

    def get_test_modules(self):
        return super().get_test_modules() | {'communication'}

    def test_publisher(self):
        publisher = Publisher()
        topic = "test_topic"

        with patch(Publisher.__module__ + '.NioPublisher') as communication:
            self.configure_block(publisher, {"topic": topic})
            communication.assert_called_once_with(topic=topic)
            communication.return_value.open.assert_called_once_with()

            publisher.start()

            # now it can process signals
            signals = [Signal()]
            publisher.process_signals(signals)
            communication.return_value.send.assert_called_once_with(signals)

            publisher.stop()
            communication.return_value.close.assert_called_once_with()

    def test_subscriber(self):
        subscriber = Subscriber()
        topic = "test_topic"

        with patch(Subscriber.__module__ + '.NioSubscriber') as communication:
            self.configure_block(subscriber, {"topic": topic})
            communication.assert_called_once_with(ANY, topic=topic)

            subscriber.start()
            communication.return_value.open.assert_called_once_with()

            # call the subscriber handler with a signal
            communication.call_args[0][0]([Signal({"a": "signal"})])
            self.assert_num_signals_notified(1)

            subscriber.stop()
            communication.return_value.close.assert_called_once_with()

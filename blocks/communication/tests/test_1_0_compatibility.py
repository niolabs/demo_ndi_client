from unittest.mock import patch, Mock

from nio.testing.block_test_case import NIOBlockTestCase

from ..publisher import Publisher
from ..subscriber import Subscriber
from ..local_publisher import LocalPublisher
from ..local_subscriber import LocalSubscriber


class Test_1_0_Compatibility(NIOBlockTestCase):
    """ Asserts that new block versions accept older comm. module
    """

    def get_test_modules(self):
        return super().get_test_modules() | {'communication'}

    def test_compatibility(self):
        self._test_class(Publisher, ".NioPublisher")
        self._test_class(LocalPublisher, ".NioPublisher")
        self._test_class(Subscriber, ".NioSubscriber")
        self._test_class(LocalSubscriber, ".NioSubscriber")

    def _test_class(self, block_type, comm_module_class):
        block_instance = block_type()

        # simulates old interface
        def comm_module_block_open():
            self._old_version_called = True

        self._old_version_called = False
        with patch(block_type.__module__ + comm_module_class) as communication:
            publisher_mock = Mock()
            publisher_mock.open = comm_module_block_open

            communication.return_value = publisher_mock

            self.configure_block(block_instance, {"topic": "test_topic"})
            self.assertTrue(self._old_version_called)

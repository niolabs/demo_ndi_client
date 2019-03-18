from unittest.mock import Mock

from nio.block.base import Base
from nio.testing.block_test_case import NIOBlockTestCase

from ..connectivity import PubSubConnectivity


class MyPubSubConnectivity(PubSubConnectivity, Base):
    pass


class TestConnectivity(NIOBlockTestCase):

    def get_test_modules(self):
        return super().get_test_modules() | {'communication'}

    def test_connected(self):
        connectivity = MyPubSubConnectivity()

        # setup mocks
        connectivity.logger = Mock()
        connectivity._connected_event = Mock()
        connectivity._connected_event.wait = Mock(return_value=False)
        connectivity._notify_disconnection = Mock()
        is_connected = Mock(return_value=True)

        connectivity.conn_configure(is_connected)
        self.assertTrue(connectivity._connected)
        # no waiting, notification, etc.
        self.assertEqual(connectivity._connected_event.wait.call_count, 0)
        self.assertEqual(connectivity._notify_disconnection.call_count, 0)

    def test_disconnections(self):
        connectivity = MyPubSubConnectivity()
        # setup mocks
        connectivity.logger = Mock()
        connectivity._connected_event = Mock()
        connectivity._connected_event.wait = Mock(return_value=False)
        connectivity.notify_management_signal = Mock()
        # not connected during configure
        is_connected = Mock(return_value=False)

        connectivity.conn_configure(is_connected)
        self.assertFalse(connectivity._connected)
        self.assertEqual(connectivity._connected_event.wait.call_count, 1)
        self.assertEqual(connectivity.notify_management_signal.call_count, 1)

        # simulate restoring connection
        connectivity.conn_on_connected()
        self.assertTrue(connectivity._connected)
        self.assertEqual(connectivity._connected_event.set.call_count, 1)
        self.assertEqual(connectivity.notify_management_signal.call_count, 2)

        # simulate losing connection
        connectivity.conn_on_disconnected()
        self.assertFalse(connectivity._connected)
        self.assertEqual(connectivity._connected_event.clear.call_count, 1)
        self.assertEqual(connectivity.notify_management_signal.call_count, 3)

    def test_invalid_block(self):
        # Assert that must be a block instance
        with self.assertRaises(ValueError):
            PubSubConnectivity()

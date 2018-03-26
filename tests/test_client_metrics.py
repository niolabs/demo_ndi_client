from service_tests.service_test_case import NioServiceTestCase
from nio.signal.base import Signal
from unittest.mock import patch, MagicMock


class TestClientMetrics(NioServiceTestCase):

    service_name = 'ClientMetrics'
    instance = 'test'
    cpu_signal = [Signal({'cpu_limit': 25})]
    down_signal = [Signal({'down_limit': -1})]
    up_signal = [Signal({'up_limit': -2})]
    instance_tag = 'edge|laptop'
    project_url = 'https://www.thisisatest/niolabs.com'

    def publisher_topics(self):
        """Topics this service publishes to"""
        return ['dni.client_state', 'dni.client_status.123456789']

    def subscriber_topics(self):
        """Topics this service subscribes to"""
        return ['dni.admin_limits', 'dni.selected_client.' + hex(__import__('uuid').getnode())[2:].upper()]

    def env_vars(self):
        return {
                'INSTANCE_TAG': self.instance_tag,
                'PROJECT_URL': self.project_url
                }

    def mock_blocks(self):
        return {'CPUPercentage': lambda signals: self._mock_metrics(),
                'GetOS': lambda signals: self._mock_specs()}

    def _mock_metrics(self):
        self.notify_signals('CPUPercentage',
                            [Signal({'cpu_percentage_overall': 50,
                                     'net_io_counters_bytes_sent': 100,
                                     'net_io_counters_bytes_recv': 200,
                                     'virtual_memory_available': 1e5,
                                     'virtual_memory_total': 1e10,
                                     'virtual_memory_used': 6e9})])
    def _mock_specs(self):
        self.notify_signals('GetOS',
                            [Signal({'system': 'Linux',
                                     'cores': 4,
                                     'processor': 'Intel Core iPi @ 2.3GHz',
                                     'node': self.instance,
                                     'MAC': '12341234'})])

    @patch('socket.gethostname')
    def test_client_states(self, mock_hostname):
        mock_hostname.return_value = self.instance
        for block in self._blocks:
            self._blocks[block].logger = MagicMock()
        self.assertEqual(self.block_configs['ClientState']['group_by'],
                         "{{ __import__('socket').gethostname() }}")
        # Wait for sleep block
        self._scheduler.jump_ahead(1)
        # First Signal is Excluded on the Network Side
        self._scheduler.jump_ahead(1)
        # self.assert_num_signals_published(1)
        self.assertDictEqual(
            self.published_signals[-1].to_dict(),
            {'cpu_state': False,
             'down_state': False,
             'up_state': False,
             'CPU': {'clock': 2300.0, 'cores': 4, 'used': 50},
             'RAM': {'available': 3.725290298461914,
                     'total': 9.313225746154785,
                     'used': 5.587935447692871},
             'os': 'Linux',
             'MAC': '12341234',
             'tag': ['edge', 'laptop'],
             'project': 'https://www.thisisatest/niolabs.com',
             'name': self.instance,
             'prev_state': None,
             'state': {'cpu_state': False, 'down_state': False, 'up_state': False},
             'group': self.instance})
        # Wait and make sure nothing is published until state change
        self._scheduler.jump_ahead(1)
        self.publish_signals('dni.admin_limits', self.cpu_signal)
        self.publish_signals('dni.admin_limits', self.down_signal)
        self.publish_signals('dni.admin_limits', self.up_signal)
        self._scheduler.jump_ahead(1)
        self.assert_num_signals_published(2)
        self.assertDictEqual(
            self.published_signals[-1].to_dict(),
            {'cpu_state': True,
             'down_state': True,
             'up_state': True,
             'CPU': {'clock': 2300.0, 'cores': 4, 'used': 50},
             'RAM': {'available': 3.725290298461914,
                     'total': 9.313225746154785,
                     'used': 5.587935447692871},
             'os': 'Linux',
             'MAC': '12341234',
             'tag': ['edge', 'laptop'],
             'project': 'https://www.thisisatest/niolabs.com',
             'prev_state': {'cpu_state': False, 'down_state': False, 'up_state': False},
             'state': {'cpu_state': True, 'down_state': True, 'up_state': True},
             'name': self.instance,
             'group': self.instance,
            })
        # Test for Exceptions from only receiving one limit from subscriber
        for block in self._blocks:
            self.assertFalse(self._blocks[block].logger.exception.call_count)

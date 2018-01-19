from service_tests.service_test_case import NioServiceTestCase
from nio.signal.base import Signal
from unittest.mock import patch, MagicMock


class TestClientMetrics(NioServiceTestCase):

    service_name = 'ClientMetrics'
    instance = 'test'
    cpu_signal = [Signal({'cpu_limit': 25})]
    down_signal = [Signal({'down_limit': -1})]
    up_signal = [Signal({'up_limit': -2})]
    ram_signal = [Signal({'ram_limit': 1})]
    instance_tag = 'edge|laptop'
    project_url = 'https://www.thisisatest.niolabs.com'

    def publisher_topics(self):
        """Topics this service publishes to"""
        return ['dni.client_state.' + hex(__import__('uuid').getnode())[2:].upper(),
                'dni.client_stats.' + hex(__import__('uuid').getnode())[2:].upper()]

    def subscriber_topics(self):
        """Topics this service subscribes to"""
        return ['dni.admin_limits', 'dni.newui']

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
                                     'virtual_memory_used': 6e9,
                                     'disk_usage_free': 1e9,
                                     'disk_usage_percent': 41.7,
                                     'disk_usage_total': 16e9})])
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
                         "{{ $name }}")
        # Wait for sleep block
        self._scheduler.jump_ahead(1)
        # First Signal is Excluded on the Network Side
        self._scheduler.jump_ahead(1)
        self.assert_num_signals_published(2)
        self.assertDictEqual(
            self.published_signals[0].to_dict(),
            {
             'CPU': {'clock': 2300.0, 'cores': 4, 'used': 50},
             'RAM': {'available': 3.73,
                     'total': 9.31,
                     'used': 5.59},
             'disk': {'total': 16.0, 'used': 41.7, 'available': 1.0},
             'MAC': '12341234',
             'network': {'down': 0.0, 'up': 0.0},
             'name': self.instance,
             'violations': {'cpu': False, 'down': False, 'up': False, 'ram': False},
             })
        self.assertDictEqual(
            self.published_signals[1].to_dict(),
            {
             'os': 'Linux',
             'name': self.instance,
             'disk': {'used': 41.7, 'total': 16.0, 'available': 1.0},
             'prev_state': None,
             'state': {'cpu': False, 'up': False, 'ram': False, 'down': False},
             'MAC': '12341234',
             'group': 'test',
             'tag': ['edge', 'laptop'],
             'violations': {'cpu': False, 'up': False, 'ram': False, 'down': False}
            }
        )
        # Wait and make sure nothing is published until state change
        #self._scheduler.jump_ahead(1)
        self.publish_signals('dni.admin_limits', self.cpu_signal)
        self.publish_signals('dni.admin_limits', self.down_signal)
        self.publish_signals('dni.admin_limits', self.up_signal)
        self.publish_signals('dni.admin_limits', self.ram_signal)

        self._scheduler.jump_ahead(1.5)
        self.assert_num_signals_published(4)
        self.assertDictEqual(
            self.published_signals[2].to_dict(),
            {'violations': {'cpu': True, 'down': True, 'up': True, 'ram': False},
             'CPU': {'clock': 2300.0, 'cores': 4, 'used': 50},
             'RAM': {'available': 3.73,
                     'total': 9.31,
                     'used': 5.59},
             'MAC': '12341234',
             'name': self.instance,
             'network': {'down': 0.0, 'up': 0.0},
             'disk': {'available': 1.0, 'total': 16.0, 'used': 41.7}
            })
        print(self.published_signals[3].to_dict())
        self.assertDictEqual(
            self.published_signals[3].to_dict(),
            {
             'os': 'Linux',
             'name': self.instance,
             'disk': {'used': 41.7, 'total': 16.0, 'available': 1.0},
             'prev_state': {'down': False, 'cpu': False, 'ram': False, 'up': False},
             'state': {'cpu': True, 'up': True, 'ram': False, 'down': True},
             'MAC': '12341234',
             'group': 'test',
             'tag': ['edge', 'laptop'],
             'violations': {'cpu': True, 'up': True, 'ram': False, 'down': True}
            }
        )
        # Test for Exceptions from only receiving one limit from subscriber
        # for block in self._blocks:
        #     self.assertFalse(self._blocks[block].logger.exception.call_count)

from threading import Event
from unittest.mock import patch

from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase
from nio.signal.base import Signal
from nio.util.discovery import not_discoverable

from ..host_metrics_block import HostMetrics


@not_discoverable
class EventMetrics(HostMetrics):

    def __init__(self, e):
        super().__init__()
        self._e = e

    def _collect_and_notify(self):
        super()._collect_and_notify()
        self._e.set()


class TestHostMetricsBlock(NIOBlockTestCase):

    def setUp(self):
        super().setUp()
        self.expected = [
            'cpu_percentage',
            'virtual_memory',
            'swap_memory',
            'disk_usage',
            'disk_io_counters',
            'net_io_counters'
        ]

    def test_generate_metrics(self):
        event = Event()
        blk = EventMetrics(event)
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals([Signal()])
        event.wait(1)
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertTrue(self.last_notified)
        for k in self.last_notified[DEFAULT_TERMINAL][0].to_dict():
            for idx, f in enumerate(self.expected):
                if k.startswith(f):
                    break
                elif idx == len(self.expected)-1:
                    raise AssertionError("Unexpected report key '%s'" % k)

    @patch(HostMetrics.__module__ + '.Sensors.read')
    def test_sensors(self, patch_read):
        event = Event()
        blk = EventMetrics(event)
        self.configure_block(blk, {
            "menu": {
                "sensors": True,
                "cpu_perc": False,
                "virtual_mem": False,
                "swap_mem": False,
                "disk_usage": False,
                "disk_io_ct": False,
                "net_io_ct": False
            }
        })
        patch_read.side_effect = self._sample_sensors_output
        blk.start()
        blk.process_signals([Signal()])
        event.wait(1)
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertTrue(self.last_notified)
        self.assertDictEqual(self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
                             {'sensors_acpitz-virtual-0_temp1_input': 26.800,
                              'sensors_acpitz-virtual-0_temp1_max': 105.000})

    def _sample_sensors_output(self, result):
        '''
        acpitz-virtual-0
        Adapter: Virtual device
        temp1:
          temp1_input: 26.800
          temp1_crit: 90.000

        coretemp-isa-0000
        Adapter: ISA adapter
        Core 0:
          temp2_input: 43.000
          temp2_max: 105.000
          temp2_crit: 105.000
          temp2_crit_alarm: 0.000
        Core 1:
          temp3_input: 43.000
          temp3_max: 105.000
          temp3_crit: 105.000
          temp3_crit_alarm: 0.000
        Core 2:
          temp4_input: 42.000
          temp4_max: 105.000
          temp4_crit: 105.000
          temp4_crit_alarm: 0.000
        Core 3:
          temp5_input: 42.000
          temp5_max: 105.000
          temp5_crit: 105.000
          temp5_crit_alarm: 0.000
        '''
        result['sensors_acpitz-virtual-0_temp1_input'] = 26.800
        result['sensors_acpitz-virtual-0_temp1_max'] = 105.000

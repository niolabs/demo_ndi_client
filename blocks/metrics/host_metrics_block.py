import ctypes
import os
import platform
import re
import subprocess
from datetime import datetime
import psutil

from nio.block.base import Block
from nio.command import command
from nio.properties.bool import BoolProperty
from nio.properties.holder import PropertyHolder
from nio.properties.object import ObjectProperty
from nio.properties.version import VersionProperty
from nio.signal.base import Signal

from .sensors import Sensors

RETRY_LIMIT = 3


class Menu(PropertyHolder):

    cpu_perc = BoolProperty(title='CPU Percentage', default=True)
    virtual_mem = BoolProperty(title='Virtual Memory', default=True)
    swap_mem = BoolProperty(title='Swap Memory', default=True)
    disk_usage = BoolProperty(title='Disk Usage', default=True)
    disk_io_ct = BoolProperty(title='Disk I/O Stats', default=True)
    net_io_ct = BoolProperty(title='Network I/O Stats', default=True)

    sensors = BoolProperty(title='Sensors', default=False)

    # a fairly long list in the general case. not included by default
    pids = BoolProperty(title='Process Identifiers', default=False)

    # this requires superuser priviledges and dumps a whole ton of
    # data. Maybe unnecessary? Not included by default
    skt_conns = BoolProperty(title='Socket Connections', default=False)


@command('platform')
@command('timestamp')
@command('cpu')
@command('report')
class HostMetrics(Block):

    version = VersionProperty("0.1.0")
    menu = ObjectProperty(Menu, title='Menu', default=Menu())

    def __init__(self):
        super().__init__()
        self._retry_count = 0

    def process_signals(self, signals):
        self._collect_and_notify()

    def timestamp(self):
        '''returns the current system timestamp'''
        return datetime.isoformat(datetime.utcnow())

    def _get_processor(self):
        '''Get type of processor
        http://stackoverflow.com/questions/4842448/
        getting-processor-information-in-python
        '''
        out = None
        if platform.system() == "Windows":
            out = platform.processor()
        elif platform.system() == "Darwin":
            path = os.environ['PATH']
            os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
            try:
                command = "sysctl -n machdep.cpu.brand_string"
                out = subprocess.check_output(command, shell=True)\
                    .strip().decode()
            finally:
                os.environ['PATH'] = path
        elif platform.system() == "Linux":
            command = "cat /proc/cpuinfo"
            all_info = subprocess.check_output(command, shell=True)\
                .strip().decode()
            for line in all_info.split("\n"):
                if "model name" in line:
                    out = re.sub(".*model name.*:", "", line, 1)

        if out is None:
            return platform.processor()
        else:
            return out

    def platform(self):
        '''Returns platform data
        '''
        out = {key: getattr(platform, key)() for key in
               ('machine', 'version', 'platform', 'dist', 'system')}
        out['python'] = {key: getattr(platform, "python_" + key)() for key in
                         (
                             'implementation',
                             'compiler',
                             'version',
                             'version_tuple'
                         )}
        out['python']['architecture'] = int(ctypes.sizeof(ctypes.c_voidp) * 8)
        out['processor'] = self._get_processor()
        out['cores'] = len(psutil.cpu_percent(percpu=True))
        return out

    def cpu(self):
        '''returns the overall cpu usage'''
        return psutil.cpu_percent(percpu=False)

    def report(self):
        return self._collect_stats()

    def _collect_and_notify(self):
        stats = self._collect_stats()
        if stats:
            self.notify_signals([Signal(stats)])

    def _collect_stats(self):
        result = {}

        try:
            # CPU usage statistics
            if self.menu().cpu_perc():
                base = 'cpu_percentage'
                fields = ['overall', 'per_cpu']
                for idx, f in enumerate(fields):
                    data = psutil.cpu_percent(percpu=bool(idx))
                    result["{0}_{1}".format(base, f)] = data

            # Virtual memory usage
            if self.menu().virtual_mem():
                self._collect_results('virtual_memory', result)

            # Swap memory usage
            if self.menu().swap_mem():
                self._collect_results('swap_memory', result)
                # result['swap_memory'] = psutil.swap_memory()._asdict()

            # Disk usage
            if self.menu().disk_usage():
                self._collect_results('disk_usage', result, ['/'])

            # Disk I/O statistics
            if self.menu().disk_io_ct():
                self._collect_results('disk_io_counters', result)

            # Net I/O statistics
            if self.menu().net_io_ct():
                self._collect_results('net_io_counters', result)

            # Sensors statistics - disabled by default.
            # Requires [lm-sensors](http://www.lm-sensors.org/)
            if self.menu().sensors():
                self._collect_sensors_results(result)

            # Process IDs - this dumps a big list and is disabled by default
            if self.menu().pids():
                result['process_identifiers'] = psutil.pids()

            # Socket Connections - dumps a big list and requires superuser
            # also disabled by default. Dumps a list of dictionaries; this
            # approach won't look very nice in the database, but is generally
            # quite long and not usually used.
            if self.menu().skt_conns():
                result['network_connections'] = \
                    [self.native_dict(skt._asdict())
                     for skt in psutil.net_connections()]

        except Exception as e:
            self.logger.error(
                "While processing system metrics: {0}".format(str(e))
            )
            if self._retry_count < RETRY_LIMIT:
                self._retry_count += 1
                return self._collect_stats()
            else:
                self.logger.error(
                    "System report failed {0} times, aborting...".format(
                        RETRY_LIMIT)
                )
                self._retry_count = 0
                return None
        else:
            self._retry_count = 0
            return result

    def _collect_results(self, base, result, args=[]):
        ''' Helper function to flatten the data for each psutil result

        '''
        data = getattr(psutil, base)(*args)._asdict()
        for f in data.keys():
            result['{0}_{1}'.format(base, f)] = data[f]

    def _collect_sensors_results(self, result):
        try:
            self.logger.debug('Reading sensors')
            sensors = Sensors()
            sensors.read(result)
        except subprocess.CalledProcessError:
            self.logger.exception('Looks like lm-sensors is not installed')
        except:
            self.logger.exception('Unexpected failure reading sensors')

    def _subprocess_command(self, command):
        out = None
        try:
            out = subprocess.check_output(command, shell=True).strip().decode()
            self.logger.debug('Command output: {}: {}'.format(command, out))
        except:
            self.logger.exception(
                'Failed running subprocess command: {}'.format(command))
        return out

    def native_dict(self, obj):
        return {k: obj[k] for k in obj}

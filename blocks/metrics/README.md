HostMetrics
===========
Get general statistics about the computer.

Properties
----------
- **menu**: Flags for turning off/on various metrics.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: An attribute is added for each metric read. Attribute names are the menu name followed by an underscore and then then specific metric name.

Commands
--------
- **cpu**: Returns the overall cpu usage.
- **platform**: Returns the platform data.
- **report**: Returns an overall report of the gathered statistics.
- **timestamp**: Returns the current system timestamp.


Output Examples
---------------
When reading 'CPU Percentage':
```
{
    'cpu_percentage_overall': 23.2,
    'cpu_percentage_per_cpu': [39.6, 2.5, 45.3, 6.0, 41.4, 4.6, 41.0, 5.6]
}
```
When reading *sensors*, the lm-sensors command `sensors -u` is executed and
parsed. The attributes on the signal are similar to the psutil attributes,
taking on the format of the word 'sensors', followed by the adapter name and
temperature name, separated by an underscore. For example when `sensors -u`
returns:
```
acpitz-virtual-0
Adapter: Virtual device
temp1:
  temp1_input: 26.800
coretemp-isa-0000
Adapter: ISA adapter
Core 0:
  temp2_input: 43.000
  temp2_max: 105.000
```
The output signal would look like:
```
{
    'sensors_acpitz-virtual-0_temp1_input': 26.8,
    'sensors_coretemp-isa-0000_temp2_input': 43.0,
    'sensors_coretemp-isa-0000_temp2_max': 105.0
}
```

ProcessMetrics
==============
Get statistics about a process running on the computer.

Properties
----------
- **menu**: Flags for turning off/on various metrics.
- **pid**: Process identifier for metrics to be queried on.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: A signal with metrics about the specific process.

Commands
--------

Dependencies
------------
-   [**psutil**](https://pypi.python.org/pypi/psutil)

Output Examples
---------------
Metrics about the process.
```
{
  'pid': '636',
  'cpu_percentage': 0.0,
  'cmd_line': '/Applications/TestApp.app',
  'num_ctx_switches': pctxsw(voluntary=2623955, involuntary=0),
  'memory_percent': 6.918835639953613,
  'num_fds': 137,
  'virtual_memory': 8270610432,
  'is_running': True,
  'children': [<psutil.Process(pid=645, name='fsnotifier') at 4384871256>]
}
```
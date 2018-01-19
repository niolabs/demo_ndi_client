HostSpecs
=========
Get general specifications of the nio instance host.

Properties
----------
- **menu**: Flags for turning off/on various specs.
- **machine**: Returns the hardware system architecture.
- **platform**: Returns the full platform information, including OS type, version, distribution in addition to hardware architecture.
- **os_version**: Returns the operating system version.
- **dist**: Returns the operating system distribution.
- **system**: Returns the operating system type.
- **python**: Returns information regarding the running python version.  This includes the compiler, version, implementation type, and architecture.
- **processor**: Returns the processor type and number of cores.
- **node**: Returns the network name/hostname of the nio instance host.

Inputs
------
- **default**: Any list of signals

Outputs
-------
- **default**: An attribute is added for each specification read. Attribute names are the menu name followed by an underscore and then then specific specification.

Commands
--------
None

Dependencies
------------
psutil

Output Examples
---------------
When reading 'Python Information':
```
{
  'python': {
    'compiler': 'GCC 4.9.2',
    'version': '3.5.2',
    'implementation': 'CPython',
    'architecture': 64
  }
}
```
When reading 'Hardware Platform':
```
{
  'platform': 'Linux-4.9.49-moby-x86_64-with-debian-8.7'
}
```
When reading 'Processor Type':
```
{
  'cores': 4,
  'processor': ' Intel(R) Core(TM) i7-4770HQ CPU @ 2.20GHz'
}
```

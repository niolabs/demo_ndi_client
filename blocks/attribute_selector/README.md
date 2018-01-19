AttributeSelector
=================
This block is used to whitelist or blacklist incoming signal attributes and notify the resulting modified signals.

Properties
----------
- **attributes**: Specify any incoming signal attributes to ignore or allow depending on specified behavior.
- **mode**: Specify whitelist or blacklist behavior.

Inputs
------
- **default**: Any list of signals

Outputs
-------
- **default**: The input list of signals but with modified attributes depending on whitelist/blacklist selections.

Commands
--------

Dependencies
------------
None

Blacklist:
----------
The block will emit all incoming attributes besides those specified in the
config. If a specified attribute doesn't exist in the signal, it is ignored.
If only invalid attributes are specified, the original signal is notified.

Whitelist:
----------
The block will only emit those signals that are specified in the config.
If a specified attribute doesn't exist in the signal, it is ignored.
If only invalid attributes are specified, a blank signal is notified.


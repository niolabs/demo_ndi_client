CounterIntervalSimulator
========================
Simulates and notifies a signal every [interval] seconds.

Properties
----------
- **attr_name**: The name of the attribute on the Signal.
- **attr_value**: The value assigned to the simulated attribute.
- **interval**: How often should the block notify signals.
- **num_signals**: How many signals get notified at once.
- **total_signals**: The maximum number of signals to notify overall. If less than 0 (-1 by default), then the trigger will continue to notify indefinitely until the block is stopped.

Inputs
------

Outputs
-------
- **default**: The simulated signals.

Commands
--------

CounterSafeSimulator
====================
Simulates and notifies a signal every [interval] seconds, even if not all signals have been simulated.  If the max_count is too high, the block will notify a signal with however many signals it was able to create during the defined interval.

Properties
----------
- **attr_name**: The name of the attribute on the Signal.
- **attr_value**: The value assigned to the simulated attribute.
- **interval**: How often should the block notify signals.
- **max_count**: Maximum signals to notify — the block will never notify more signals than this count every interval. However, if the number is too high for it to create, it may return less than this number. The only guarantee made by this block is that a notification will happen every interval.

Inputs
------

Outputs
-------
- **default**: The simulated signals.

Commands
--------

FileIntervalSimulator
=====================
Creates signals as defined by a json file. The file must be a list of dictionaries where each dictionary is a nio Signal. The file should be loadable using `json.load`.  Each call to generate_signals will return a signal from the list loaded in from the json file.  When asked to generate -1 signals, it will generate all signals in the file.

Properties
----------
- **interval**: How often should the block notify signals.
- **num_signals**: How many signals get notified at once.
- **random_selection**: Whether or not to randomly pull from the file. If unchecked, the simulator will iterate through the file sequentially.
- **signals_file**: The location of the file containing a list of signals. It can be an absolute file location, relative to the root project directory or relative to the block path.
- **total_signals**: The maximum number of signals to notify overall. If less than 0 (-1 by default), then the trigger will continue to notify indefinitely until the block is stopped.

Inputs
------

Outputs
-------
- **default**: The simulated signals.

Commands
--------

IdentityCronSimulator
=====================
Simulate and notify signals according to a cron-like timetable

Properties
----------
- **cron**: 
- **num_signals**: How many signals get notified at once.

Inputs
------

Outputs
-------
- **default**: The simulated signals.

Commands
--------

IdentityIntervalSimulator
=========================
Simulates and notifies empty signals.

Properties
----------
- **interval**: How often should the block notify signals.
- **num_signals**: How many signals get notified at once.
- **total_signals**: The maximum number of signals to notify overall. If less than 0 (-1 by default), then the trigger will continue to notify indefinitely until the block is stopped.

Inputs
------

Outputs
-------
- **default**: The simulated signals.

Commands
--------


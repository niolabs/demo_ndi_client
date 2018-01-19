Filter
======

A block for filtering signal objects based on a list of plaintext conditions, evaluated as Python code.

Properties
----------

-   **conditions**: List of queries.
-   **operator**: ALL or ANY. Determines whether all or any of the conditions must be satisfied for a signal to pass the filter. If `ALL`, signals output to `true` if every `condition` is true (or if no conditions). If `Any`, signals output to `false` if every `condition` is false (or if no conditions).

Dependencies
------------
None

Commands
--------
None

Input
-----
Any list of signals.

Output
------
Every signal is output to either `true` or `false`.

### true

If **operator** is `ALL` then signals are output here when all **conditions** are `true`.

If **operator** is `ANY` then signals are output here when any **conditions** are `true`.

### false

If **operator** is `ALL` then signals are output here when any **conditions** are `false`.

If **operator** is `ANY` then signals are output here when all **conditions** are `false`.

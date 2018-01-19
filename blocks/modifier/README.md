Modifier
========
Adds attributes to existing signals as specified. If the `exclude` flag is set, the block instantiates new (generic) signals and passes them along with *only* the specified `fields`.

Properties
----------
- **exclude**: If `True`, output signals only contain the attributes specified by `fields`.
- **fields**: List of attribute names and corresponding values to add to the incoming signals.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: One signal for every incoming signal, modified according to `fields` and `exclude`.

Commands
--------


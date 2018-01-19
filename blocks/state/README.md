AppendState
===========
Maintains a state and when state changes, a signal is notified that contains the `state` and `prev_state`.

Properties
----------
- **backup_interval**: Interval at which state is saved to disk.
- **group_by**: What to group the signals by. A different state will be maintained for each group
- **initial_state**: The state when none has been set by an incoming signal. If the `initial_state` is a python expression, it is evaluated at configuration. For example, if the `initial_state` is configured as `{{ datetime.datetime.utctime() }}`, the value of `initial_state` will the be time at configuration.
- **load_from_persistence**: Upon restart, block will load the previous state and resume operation as if restart did not happen.
- **state_expr**: Property that evaluates to state. If the expression cannot be evaluated, the state will not change.
- **state_name**: String property that is the name of the appended state

Inputs
------
- **getter**: Any list of signals. Signals that get assigned a state and/or pass through the block.
- **setter**: Signals passed to this input set the state of the block. Each signal is evaluated against `state_expr` to determine the new state of the block for the signal's group.

Outputs
-------
- **default**: Non state setting signals are passed through with state set to the attribute `state_name`.

Commands
--------
- **current_state**: Get the current state of the block is applying to the signals
- **groups**: Display the current groupings of signals.

StateChange
===========
Maintains a state and when state changes, a signal is notified that contains the `state` and `prev_state`.

Properties
----------
- **backup_interval**: Interval at which state is saved to disk.
- **exclude**: Select whether you want to exclude other signals. If checked, the only output will be `state` and `prev_state`. If not checked, `state` and `prev_state` will be appended onto the incoming signal.
- **group_by**: What to group the signals by. A different state will be maintained for each group
- **initial_state**: The state when none has been set by an incoming signal. If the `initial_state` is a python expression, it is evaluated at configuration. For example, if the `initial_state` is configured as `{{ datetime.datetime.utctime() }}`, the value of `initial_state` will the be time at configuration.
- **load_from_persistence**: Upon restart, block will load the previous state and resume operation as if restart did not happen.
- **state_expr**: Property that evaluates to state. If the expression cannot be evaluated, the state will not change.
- **state_name**: String property that is the name of the appended state

Inputs
------
- **default**: Signal with attribute to be set and watched as state.

Outputs
-------
- **default**: When state changes, a signal is notified with attributes `state`, `prev_state`, and `group`. If `exclude` is _unchecked_ then the signal that changed the state will have the attributes added to it.

Commands
--------
- **current_state**: Get the current state of the block is applying to the signals
- **groups**: Display the current groupings of signals.

Switch
======
getter signals pass through to the *true* output if the last *setter* signal set the state to `True`. Else, the signals to getter pass through to the false output.

Properties
----------
- **backup_interval**: Interval at which state is saved to disk.
- **group_by**: What to group the signals by. A different state will be maintained for each group
- **initial_state**: The state when none has been set by an incoming signal. If the `initial_state` is a python expression, it is evaluated at configuration. For example, if the `initial_state` is configured as `{{ datetime.datetime.utctime() }}`, the value of `initial_state` will the be time at configuration.
- **load_from_persistence**: Upon restart, block will load the previous state and resume operation as if restart did not happen.
- **state_expr**: Property that evaluates to state. If the expression cannot be evaluated, the state will not change.

Inputs
------
- **getter**: Any list of signals. Signals that get assigned a state and/or pass through the block.
- **setter**: Signals passed to this input set the state of the block. Each signal is evaluated against `state_expr` to determine the new state of the block for the signal's group.

Outputs
-------
- **false**: getter signals pass through to the false output by default until state is changed to `True`.
- **true**: getter signals pass through to the true output if the last setter signal set the state to `True`

Commands
--------
- **current_state**: Get the current state of the block is applying to the signals
- **groups**: Display the current groupings of signals.


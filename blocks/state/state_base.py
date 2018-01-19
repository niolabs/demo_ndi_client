from copy import copy
from collections import defaultdict
from nio.signal.base import Signal
from nio.block.base import Block
from nio.command import command
from nio.types.base import Type
from nio.command.params.base import Parameter
from nio.properties import Property
from nio.properties.version import VersionProperty
from threading import Lock
from nio.modules.web.http import HTTPNotFound
from nio.block.mixins.group_by.group_by import GroupBy
from nio.block.mixins.persistence.persistence import Persistence
from nio.util.discovery import not_discoverable


@not_discoverable
@command('current_state', Parameter(Type, "group", allow_none=True))
class StateBase(Persistence, GroupBy, Block):

    """ A base block mixin for keeping track of state """

    state_expr = Property(
        title='State ', default='{{ $state }}', allow_none=True)
    initial_state = Property(
        title='Initial State', default='{{ None }}', allow_none=True)
    version = VersionProperty('0.1.0')

    def __init__(self):
        super().__init__()
        self._initial_state = None
        self._state_locks = defaultdict(Lock)
        self._safe_lock = Lock()
        self._states = {}

    def persisted_values(self):
        """Persist states using block mixin."""
        return ["_states"]

    def configure(self, context):
        super().configure(context)
        # Store a cached copy of what a new state should look like
        self._initial_state = self.initial_state(Signal())

    def get_state(self, group):
        """ Return the current state for a group.

        If the state has not been set yet, this function will return the
        initial state configured for the block. It will also set that as the
        state.
        """
        if group not in self._states:
            self._states[group] = copy(self._initial_state)
        return self._states[group]

    def process_signals(self, signals, input_id=None):
        """ Process incoming signals.

        This block is a helper, it will just call _process_group and
        notify any signals that get appeneded to the to_notify list.

        Most likely, _process_group will be overridden in subclasses instead
        of this method.
        """
        self.logger.debug(
            "Ready to process {} incoming signals".format(len(signals)))
        signals_to_notify = defaultdict(list)
        with self._safe_lock:
            group_result = self.for_each_group(
                self._process_group, signals, input_id=input_id,
                signals_to_notify=signals_to_notify)
            if group_result:
                signals_to_notify[None] = group_result
        for output_id in signals_to_notify:
            if output_id:
                self.notify_signals(signals_to_notify[output_id],
                                    output_id=output_id)
            else:
                self.notify_signals(signals_to_notify[output_id])

    def _process_group(self, signals, group, input_id, signals_to_notify=None):
        """ Implement this method in subclasses to process signals in a group.

        Return:
            list or dict(list): The list of signals to be nofified. If
                notifying to a non-default input, return a dict with the key
                as the output id.
        """
        pass

    def _process_state(self, signal, group):
        """ Changes state based on a signal and a group.

        If the signal cannot be processed, the state remains unchanged.

        Returns:
            Tuple: (prev_sate, new_state) if the state was changed
            None - if the state did not change
        """
        with self._state_locks[group]:
            prev_state = self.get_state(group)
            try:
                new_state = self.state_expr(signal)
            except:
                # expression failed so don't set a state.
                self.logger.exception(
                    "State Change failed for group {}".format(group))
                return

            if new_state != prev_state:
                # notify signal if there was a prev_state and
                # the state has changed.
                self.logger.debug(
                    "Changing state from {} to {} for group {}".format(
                        prev_state, new_state, group))
                self._states[group] = new_state

                return (prev_state, new_state)

    def current_state(self, group):
        """ Command that returns the current state of a group """
        if group is None:
            return_list = []
            with self._safe_lock:
                for group in self._states:
                    return_list.append({"group": group,
                                        "state": self._states[group]})
            return return_list
        if group in self._states:
            return {"group": group,
                    "state": self._states[group]}
        else:
            raise HTTPNotFound()

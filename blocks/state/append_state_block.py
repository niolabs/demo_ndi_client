from .state_base import StateBase
from nio.block.terminals import input
from nio.properties import StringProperty, VersionProperty


@input('setter')
@input('getter')
class AppendState(StateBase):

    """ Merge the *setter* state into *getter* signals.

    Maintains a *state* and merges that state (with name **state_name**) with
    signals that are input through the *getter* input.
    """

    state_name = StringProperty(default='state', title="State Name")
    version = VersionProperty("0.1.1")

    def _process_group(self, signals, group, input_id, signals_to_notify):
        if input_id == 'setter':
            return self._process_setter_group(signals, group)
        else:
            return self._process_getter_group(signals, group)

    def _process_getter_group(self, signals, group):
        signals_to_notify = []
        for signal in signals:
            existing_state = self.get_state(group)
            self.logger.debug(
                "Assigning state {} to signal".format(existing_state))
            setattr(signal, self.state_name(), existing_state)
            signals_to_notify.append(signal)
        return signals_to_notify

    def _process_setter_group(self, signals, group):
        for signal in signals:
            self.logger.debug("Attempting to set state")
            self._process_state(signal, group)
        return []

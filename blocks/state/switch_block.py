from nio.block.terminals import input, output
from nio.properties import VersionProperty
from .state_base import StateBase


@input('setter')
@input('getter')
@output('false')
@output('true')
class Switch(StateBase):

    """ Passthrough *getter* signals if the state is True.

    *getter* signals pass through to the *true* output if the last *setter*
    signal set the state to True. Else, the signals to *getter* pass through
    to the *false* output.
    """
    version = VersionProperty("0.1.1")

    def _process_group(self, signals, group, input_id, signals_to_notify):
        if input_id == 'setter':
            return self._process_setter_group(signals, group)
        else:
            return self._process_getter_group(
                signals, group, signals_to_notify)

    def _process_getter_group(self, signals, group, signals_to_notify):
        for signal in signals:
            if self.get_state(group):
                self.logger.debug("State is True")
                signals_to_notify['true'].append(signal)
            else:
                self.logger.debug("State is False")
                signals_to_notify['false'].append(signal)

    def _process_setter_group(self, signals, group):
        """ Process the signals from the setter input for a group.

        Add any signals that should be passed through to the to_notify list
        """
        for signal in signals:
            self.logger.debug("Attempting to set state")
            self._process_state(signal, group)
        return []

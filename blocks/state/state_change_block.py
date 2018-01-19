from nio.properties import BoolProperty, StringProperty
from nio.signal.base import Signal
from .state_base import StateBase


class StateChange(StateBase):

    """ Notifies a signal on *state* change.

    Maintains a *state*. When *state* changes, a signal is notified
    that containes the *state* and *prev_state*.

    *state* is set by the *state_expr* property. It is an expression
    property that evalues to *state*. If the expression fails,
    then the *state* remains unmodified.
    """

    state_name = StringProperty(
        default='state', title="State Name", visible=False)
    exclude = BoolProperty(default=True, title="Exclude Existing Fields")

    def _process_group(self, signals, group, input_id, signals_to_notify):
        """Process the signals for a group."""
        signals_to_notify = []
        for signal in signals:
            state_change = self._process_state(signal, group)
            if state_change is not None:
                # If we are excluding existing fields we want to add
                # the states and previous states to an empty signal
                if self.exclude():
                    signal = Signal()
                setattr(signal,
                        'prev_{}'.format(self.state_name()), state_change[0])
                setattr(signal, '{}'.format(
                    self.state_name()), state_change[1])
                setattr(signal, 'group', group)
                signals_to_notify.append(signal)
        return signals_to_notify

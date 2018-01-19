from nio.block.base import Block
from nio.signal.base import Signal
from nio.properties import Property, VersionProperty, ListProperty, \
    BoolProperty, PropertyHolder


class SignalField(PropertyHolder):
    title = Property(default='', title='Attribute Name')
    formula = Property(default='', title='Attribute Value', allow_none=True)


class Modifier(Block):

    """ A nio block for enriching signals.

    By default, the modifier block adds attributes to
    existing signals as specified. If the 'exclude' flag is
    set, the block instantiates new (generic) signals and
    passes them along with *only* the specified fields.

    Properties:
        - fields(list): List of attribute names and corresponding values to add
                        to the incoming signals.
        - exclude(bool): If `True`, output signals only contain the attributes
                   specified by `fields`.
    """

    fields = ListProperty(SignalField, title='Fields', default=[])
    exclude = BoolProperty(default=False, title='Exclude existing fields?')
    version = VersionProperty("1.0.0")

    def process_signals(self, signals):
        fresh_signals = []

        for signal in signals:

            # if we are including only the specified fields, create
            # a new, empty signal object
            tmp = Signal() if self.exclude() else signal

            # iterate over the specified fields, evaluating the formula
            # in the context of the original signal
            for field in self.fields():
                value = field.formula(signal)
                title = field.title(signal)
                setattr(tmp, title, value)

            # only rebuild the signal list if we're using new objects
            if self.exclude:
                fresh_signals.append(tmp)

        if self.exclude():
            signals = fresh_signals

        self.notify_signals(signals)

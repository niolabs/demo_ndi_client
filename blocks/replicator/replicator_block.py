from nio.block.base import Block
from nio.signal.base import Signal
from nio.util.discovery import discoverable
from nio.properties import Property, StringProperty, VersionProperty


@discoverable
class Replicator(Block):
    """Each incoming signal is replicated x times, where x
    is the length of list. Each output signal with have a
    new attribute, title, with the value of the list.

    """
    version = VersionProperty("1.0.0")
    title = StringProperty(title='Attribute Title', default='')
    list = Property(title='List', default='')

    def process_signals(self, signals):
        return_signals = []
        for signal in signals:
            try:
                values = self.list(signal)
            except Exception:
                values = [None]
                self.logger.exception("Failed to evaluate list")
            values = [None] if not values else values
            for value in values:
                sig = Signal(signal.to_dict())
                setattr(sig, self.title(), value)
                return_signals.append(sig)
        if return_signals:
            self.notify_signals(return_signals)

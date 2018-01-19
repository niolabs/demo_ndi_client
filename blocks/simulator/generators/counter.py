from itertools import chain, repeat, islice
from math import ceil
from threading import Lock

from nio import Signal
from nio.properties import PropertyHolder, ObjectProperty, IntProperty, \
    StringProperty


class Value(PropertyHolder):
    start = IntProperty(default=0, title='Start')
    end = IntProperty(default=1, title='End')
    step = IntProperty(default=1, title='Step')


class CounterGenerator():

    """A fast numeric batch generator"""

    attr_name = StringProperty(default='sim', title='Simulated Attribute')
    attr_value = ObjectProperty(Value, title='Simulated Value')

    def __init__(self):
        super().__init__()
        self.count_lock = Lock()
        self._range = None
        self._range_length = 0
        self._skip_count = 0

    def configure(self, context):
        super().configure(context)
        self._range = range(self.attr_value().start(),
                            self.attr_value().end() + 1,
                            self.attr_value().step())
        self._range_length = len(self._range)

    def generate_signals(self, n=1):
        with self.count_lock:
            # Build enough range objects to simulate n signals
            ranges = repeat(self._range, ceil(n / self._range_length) + 1)

            # Build an iterator to return the value
            # Skip some if we need to make sure we start at the right spot
            values_iterator = islice(
                chain.from_iterable(ranges), self._skip_count, None)

            # In case n is not divisible by the range length, we may need to
            # skip a number of items next time to make sure we start counting
            # in the right spot
            self._skip_count = (self._skip_count + n) % self._range_length

            return (
                Signal({name: value})
                for (name, value) in
                zip(repeat(self.attr_name(), n), values_iterator))

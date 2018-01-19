import json
import random
from os.path import isfile

from nio import Signal
from nio.properties import BoolProperty, FileProperty


class FileGenerator():
    """A generator that pull signals from a file"""

    signals_file = FileProperty(
        title='Signals File', default='signals.json')
    random_selection = BoolProperty(
        title='Choose Randomly?', default=True)

    def __init__(self):
        super().__init__()
        self._json_signals = None
        self._index = 0

    def configure(self, context):
        super().configure(context)
        self._json_signals = self._load_json_file()
        if self._json_signals is None:
            raise Exception("Couldn't find JSON signals in file")
        self.logger.debug(
            'Loaded {} signals from file'.format(len(self._json_signals)))

    def generate_signals(self, n=1):
        # If generating all signals, don't do it randomly.
        _random = False if n == -1 else self.random_selection()
        # Generate all signals if n is -1.
        n = len(self._json_signals) if n == -1 else n
        # If we didn't load signals from file, don't generate any.
        n = n if len(self._json_signals) else 0
        return [self._get_next_signal(_random) for i in range(n)]

    def _get_next_signal(self, _random=False):
        """ Get the next individual signal from the file.

        If configured to do so, this will pull randomly from the file.
        Otherwise, it will return the next one in line.
        """
        if _random:
            return Signal(random.choice(self._json_signals))
        else:
            sig = Signal(self._json_signals[self._index])
            self._increment_index()
            return sig

    def _increment_index(self):
        """ Increment the current index, rollover when necessary """
        self._index += 1
        if self._index >= len(self._json_signals):
            self._index = 0

    def _load_json_file(self):
        """Loads the configured JSON file with signals

        Returns json file or None if failed to load file.
        """

        with self.signals_file() as json_file:
            try:
                json_data = json.load(json_file)
                return json_data
            except:
                self.logger.exception('Failed to load json signals file')

    def _get_valid_file(self, *args):
        """Go through args and return the first valid file.

        Returns None if none no valid file is found.
        """
        for arg in args:
            if isfile(arg):
                return arg
        return None

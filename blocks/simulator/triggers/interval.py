from nio.modules.scheduler import Job
from nio.properties import TimeDeltaProperty, IntProperty


class IntervalTrigger():
    """Generate signals at a regular interval up to total_signals"""

    total_signals = IntProperty(title="Total Number of Signals", default=-1)
    interval = TimeDeltaProperty(title='Interval', default={'seconds': 1})

    def __init__(self):
        super().__init__()
        self.counter = None
        self._job = None

    def start(self):
        super().start()
        self.counter = 0
        # Schedule interval simulations for the future
        self._job = Job(self._simulate, self.interval(), True)
        # But also simulate right away
        self._simulate()

    def _simulate(self):
        sigs = self.generate_signals()
        # If a generator is returned, build the list
        if not isinstance(sigs, list):
            sigs = list(sigs)
        # Add however many signals were generated (in case multiple
        # signals mixin was used) to the counter and notify them
        self.counter += len(sigs)
        # self.counter - self.total_signals() yield that amount of signals that
        # should be removed
        if self.counter > self.total_signals() and self.total_signals() >= 0:
            sigs_to_remove = self.counter - self.total_signals()
            sigs = sigs[:-1 * sigs_to_remove]
        self.notify_signals(sigs)
        if self.total_signals() > 0 and \
                self.counter >= self.total_signals():
            self._job.cancel()

    def stop(self):
        """ Stop the simulator thread. """
        self._job.cancel()
        super().stop()

from threading import Event, Lock

from nio.properties import TimeDeltaProperty, IntProperty
from nio.modules.scheduler import Job
from nio.util.threading import spawn


class SafeTrigger():

    """ Guarantees notifying signals every interval, regardless of count """

    interval = TimeDeltaProperty(title='Interval', default={'seconds': 1})
    max_count = IntProperty(title='Max Count', default=1)

    def __init__(self):
        super().__init__()
        self._job = None
        self.stop_event = Event()
        self.signal_lock = Lock()

    def start(self):
        super().start()
        self._job = Job(self._emit, self.interval(), True)
        # Run an emit cycle immediately, but in a new thread since it
        # might take some time and we don't want it to hold up start
        spawn(self._emit)

    def stop(self):
        """ Stop the simulator thread and signal generation """
        if self._job:
            self._job.cancel()

        self.stop_event.set()
        super().stop()

    def _emit(self):
        """ Called every *interval* to generate then notify the signals """
        self.logger.debug("New generation cycle requested")
        count = 0
        signals = []

        # Stop any currently running simulator threads
        self.stop_event.set()
        # We only want one simulator thread simulating at a time
        with self.signal_lock:
            # Ok, we're running, so clear the event and wait
            self.stop_event.clear()
            self.logger.debug("Starting generation...")
            while count < self.max_count() and not self.stop_event.is_set():
                signals.extend(self.generate_signals(1))
                count += 1

        self.logger.debug("Notifying {} signals".format(len(signals)))
        self.notify_signals(signals)

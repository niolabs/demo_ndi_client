from collections import defaultdict
from datetime import timedelta
from time import time as _time
from threading import Lock

from nio.block.base import Block
from nio.properties import TimeDeltaProperty, VersionProperty
from nio.modules.scheduler import Job
from nio.block.mixins import Persistence


class Sleep(Persistence, Block):

    """ Sleep block.

    Emits the signals passed to it, after a given interval

    Attributes:
        interval (TimeDeltaProperty): Time period of signal emission.

    """

    interval = TimeDeltaProperty(title='Interval', default={'seconds': 1})
    version = VersionProperty("0.1.0")

    def __init__(self):
        super().__init__()
        self._signals = []
        self._signals_lock = Lock()
        self._load_signals = []

    def persisted_values(self):
        return ["_signals"]

    def configure(self, context):
        super().configure(context)
        # Save off the loaded signals to schedule on 'start'
        self._load_signals = self._signals
        self._signals = []

    def start(self):
        super().start()
        self._schedule_persistence_emits()

    def stop(self):
        self._store_signals(_time())
        super().stop()

    def process_signals(self, signals):
        # After interval, notify these signals
        signals_by_interval = self._group_signals_by_interval(signals)
        for signals in signals_by_interval.values():
            self._emit_signals_after_duration(signals,
                                              self.interval(signals[0]))

    def _group_signals_by_interval(self, signals):
        """Group signals by evaluated interval property"""
        signals_by_interval = defaultdict(list)
        for signal in signals:
            signals_by_interval[self.interval(signal)].append(signal)
        return signals_by_interval

    def _schedule_persistence_emits(self):
        """ Schedule emit jobs for signals loaded from persistence """
        ctime = _time()
        self.logger.debug(
            "Scheduling {} persisted sleep jobs".format(
                len(self._load_signals)))
        for (emit_time, signals) in self._load_signals:
            # get time to go before the signals should be notified
            duration = emit_time - ctime
            if duration > 0 and signals:
                duration = timedelta(seconds=duration)
                self._emit_signals_after_duration(signals, duration, emit_time)

    def _emit_signals_after_duration(self, signals, duration, emit_time=None):
        """ Schedule job to emit signals after duration and stores signals

        If emit_time is specified, then signals will be stored to persistence
        with that time instead of `now + duration`.

        Args:
            signals (list[Signal]): list of signals to sleep
            duration (timedelta): time to wait before emitting signals
            emit_time (float): when to emit signals (seconds since the epoch)
        """
        Job(self.notify_signals, duration, False, signals)
        emit_time = emit_time or _time() + duration.total_seconds()
        self._store_signals(emit_time, signals)

    def _store_signals(self, notify_time, signals=None):
        """ Add new signals and trim old ones before storing """
        with self._signals_lock:
            if signals:
                self._signals.append((notify_time, signals))
            self._signals = self._trim_old_signals(_time(), self._signals)

    def _trim_old_signals(self, ctime, signals):
        """ Remove signals from `signals` older than `ctime` """
        return [(t, s) for (t, s) in self._signals if ctime <= t]

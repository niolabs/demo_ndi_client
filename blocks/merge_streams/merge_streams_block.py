from collections import defaultdict
from threading import Lock

from nio.block.terminals import input
from nio.block.base import Block
from nio.signal.base import Signal
from nio.properties import VersionProperty, TimeDeltaProperty, \
    BoolProperty
from nio.modules.scheduler import Job
from nio.block.mixins.group_by.group_by import GroupBy
from nio.block.mixins.persistence.persistence import Persistence


@input('input_2')
@input('input_1', default=True)
class MergeStreams(Persistence, GroupBy, Block):

    """ Take two input streams and combine signals together. """

    expiration = TimeDeltaProperty(default={}, title="Stream Expiration")
    notify_once = BoolProperty(default=True, title="Notify Once?")
    version = VersionProperty('0.1.0')

    def _default_signals_dict(self):
        return {"input_1": {}, "input_2": {}}

    def _default_expiration_jobs_dict(self):
        return {"input_1": None, "input_2": None}

    def __init__(self):
        super().__init__()
        self._signals = defaultdict(self._default_signals_dict)
        self._signals_lock = defaultdict(Lock)
        self._expiration_jobs = defaultdict(self._default_expiration_jobs_dict)

    def persisted_values(self):
        """Persist signals only when no expiration (ttl) is configured.

        Signals at each input will be persisted between block restarts except
        when an expiration is configured. TODO: Improve this feature so signals
        are always persisted and then properly removed after loaded and the
        expiration has passed.
        """
        if self.expiration():
            return []
        else:
            return ["_signals"]

    def process_group_signals(self, signals, group, input_id):
        merged_signals = []
        with self._signals_lock[group]:
            for signal in signals:
                self._signals[group][input_id] = signal
                signal1 = self._signals[group]["input_1"]
                signal2 = self._signals[group]["input_2"]
                if signal1 and signal2:
                    merged_signal = self._merge_signals(signal1, signal2)
                    merged_signals.append(merged_signal)
                    if self.notify_once():
                        self._signals[group]["input_1"] = {}
                        self._signals[group]["input_2"] = {}
            if self.expiration():
                self._schedule_signal_expiration_job(group, input_id)
        return merged_signals

    def _merge_signals(self, signal1, signal2):
        """ Merge signals 1 and 2 and clear from memory if only notify once """
        sig_1_dict = signal1.to_dict()
        sig_2_dict = signal2.to_dict()

        self._fix_to_dict_hidden_attr_bug(sig_1_dict)
        self._fix_to_dict_hidden_attr_bug(sig_2_dict)
        merged_signal_dict = {}
        merged_signal_dict.update(sig_1_dict)
        merged_signal_dict.update(sig_2_dict)
        return Signal(merged_signal_dict)

    def _fix_to_dict_hidden_attr_bug(self, signal_dict):
        """ Remove special attributes from dictionary

        n.io has a bug when using Signal.to_dict(hidden=True). It should
        include private attributes (i.e. attributes starting withe '_') but not
        special attributes (i.e. attributes starting with '__').

        """
        for key in list(signal_dict.keys()):
            if key.startswith('__'):
                del signal_dict[key]

    def _schedule_signal_expiration_job(self, group, input_id):
        """ Schedule expiration job, cancelling existing job first """
        if self._expiration_jobs[group][input_id]:
            self._expiration_jobs[group][input_id].cancel()
        self._expiration_jobs[group][input_id] = Job(
            self._signal_expiration_job, self.expiration(), False,
            group, input_id)

    def _signal_expiration_job(self, group, input_id):
        self._signals[group][input_id] = {}
        self._expiration_jobs[group][input_id] = None

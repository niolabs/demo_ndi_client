from collections import defaultdict

from nio.block.base import Block
from nio.block.mixins.group_by.group_by import GroupBy
from nio.block.mixins.enrich.enrich_signals import EnrichSignals
from nio.properties import Property, StringProperty, \
    BoolProperty, VersionProperty


class Join(EnrichSignals, GroupBy, Block):

    """ Join block.

    Group a list of signals into one signal.
    The output signal will contain an attribute for each
    evaluated *key* and the value of that attribute will
    be a list with an item of *value* for each matching signal.

    If *one_value* is True, the Signal attributes will be just a
    single matching value instead of a list of all matching values.
    If multiple matches, then the last signal processed will be the
    value used.

    """
    key = StringProperty(
        title='Key', default="{{ $key }}")
    value = Property(
        title='Value', default="{{ $value }}", allow_none=True)
    group_attr = StringProperty(
        title="Group Attribute Name", default="group", visible=False)
    one_value = BoolProperty(title="One Value Per Key", default=False)
    version = VersionProperty("1.0.0")

    def process_signals(self, signals, input_id='default'):
        self.notify_signals(self.for_each_group(
            self._get_hash_from_group, signals))

    def _get_hash_from_group(self, signals, group):
        self.logger.debug("Processing group {} of {} signals".format(
            group, len(signals)))
        out_sig = self._perform_hash(signals)
        if out_sig:
            setattr(out_sig, self.group_attr(), group)
            return out_sig

    def _perform_hash(self, signals):
        hash_dict = defaultdict(None) if self.one_value() \
            else defaultdict(list)

        for signal in signals:
            sig_key = self.key(signal)
            sig_value = self.value(signal)

            # Add sig_value to the proper hash key
            try:
                if sig_key is not None:
                    if self.one_value():
                        hash_dict[sig_key] = sig_value
                    else:
                        hash_dict[sig_key].append(sig_value)
                else:
                    self.logger.debug("Skipping key: {}".format(sig_key))
            except:
                self.logger.exception(
                    "Failed to add value {} to key {}".format(
                        sig_value, sig_key))

        if len(hash_dict):
            return self.get_output_signal(hash_dict, signals[-1])

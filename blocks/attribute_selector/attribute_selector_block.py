from enum import Enum

from nio.signal.base import Signal
from nio.block.base import Block
from nio.properties import VersionProperty, SelectProperty, ListProperty
from nio.types import StringType


class Behavior(Enum):
    BLACKLIST = False
    WHITELIST = True


class AttributeSelector(Block):
    """
    A block for whitelisting or blacklisting incoming signals and notifying
    the rest.

    Properties:
    mode(select): select either whitelist or blacklist behavior
    attributes(list): list of incoming signal attributes to blacklist
                              or whitelist
    """

    version = VersionProperty('1.0.0')
    mode = SelectProperty(Behavior, title='Selector Mode',
                          default=Behavior.BLACKLIST)
    attributes = ListProperty(StringType,
                              title='Incoming signal attributes',
                              default=[])

    def process_signals(self, signals):
        new_sigs = []
        for signal in signals:
            sig_dict = signal.to_dict(include_hidden=True)
            attributes = set(spec for spec in self.attributes(signal))
            keep_attributes = set(sig_dict.keys()).intersection(attributes)

            if self.mode() is Behavior.WHITELIST:
                self.logger.debug('whitelisting...')

                if len(keep_attributes) < len(attributes):
                    self.logger.warning(
                        'specified an attribute that is not in the '
                        'incoming signal: {}'.format(
                            attributes.difference(keep_attributes)))

                new_sig = Signal({attr: sig_dict[attr] for attr in
                                  keep_attributes})

                self.logger.debug('Allowing incoming attributes: {}'
                                  .format(keep_attributes))

            elif self.mode() is Behavior.BLACKLIST:
                self.logger.debug('blacklisting...')

                new_sig = Signal({attr: sig_dict[attr] for attr in sig_dict
                                  if attr not in keep_attributes})

                self.logger.debug('Ignoring incoming attributes: {}'
                                  .format(keep_attributes))

            new_sigs.append(new_sig)

        self.notify_signals(new_sigs)

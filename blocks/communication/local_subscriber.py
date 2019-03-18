from base64 import b64decode
import pickle

from nio import GeneratorBlock, Signal
from nio.modules.communication.subscriber import Subscriber as NioSubscriber
from nio.properties import StringProperty, VersionProperty

from .connectivity import PubSubConnectivity


class LocalSubscriber(PubSubConnectivity, GeneratorBlock):
    """ A block for subscribing to a local nio communication channel.

    Functions regardless of communication module implementation.

    Unlike the regular Subscriber block, the one does not need data to be json
    """
    version = VersionProperty("1.1.1")
    topic = StringProperty(title="Topic", default="")
    local_identifier = StringProperty(
        title='Local Identifier', default='[[INSTANCE_ID]]', advanced=True)

    def __init__(self):
        super().__init__()
        self._subscriber = None

    def configure(self, context):
        super().configure(context)
        topic = self.topic()
        # If a local identifier was included use it as a prefix
        if self.local_identifier():
            topic = "{}.{}".format(self.local_identifier(), topic)
        self._subscriber = NioSubscriber(self._subscriber_handler, topic=topic)

        try:
            self._subscriber.open(on_connected=self.conn_on_connected,
                                  on_disconnected=self.conn_on_disconnected)
        except TypeError as e:
            self.logger.warning(
                "Connecting to an outdated communication module")
            # try previous interface
            self._subscriber.open()
            # no need to configure connectivity if not supported
            return

        # let connectivity configure
        self.conn_configure(self._subscriber.is_connected)

    def stop(self):
        """ Stop the block by closing the underlying subscriber """
        self._subscriber.close()
        super().stop()

    def _subscriber_handler(self, signals):
        try:
            signals = b64decode(signals[0].signals)
            signals = pickle.loads(signals)
        except pickle.UnpicklingError:
            self.logger.exception("Unpickling based pickle error")
        except AttributeError:
            # It's possible these came from a non-local publisher
            # This would occur in service tests or if a regular publisher
            # wanted to publish to a local topic. In the non-service test
            # case this would generally indicate bad service design but we
            # don't want to explicitly prevent/forbid it
            if (signals and
                    isinstance(signals, list) and
                    isinstance(signals[0], Signal)):
                self.notify_signals(signals)
            else:
                raise
        except TypeError:
            self.logger.exception("Unable to decode pickled signals")
        except Exception:
            self.logger.exception("Error handling signals")
        else:
            self.notify_signals(signals)

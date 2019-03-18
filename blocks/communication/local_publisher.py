from base64 import b64encode
import pickle

from nio import TerminatorBlock
from nio import Signal
from nio.modules.communication.publisher import Publisher as NioPublisher
from nio.modules.communication.publisher import PublisherError
from nio.properties import StringProperty, VersionProperty

from .connectivity import PubSubConnectivity


class LocalPublisher(PubSubConnectivity, TerminatorBlock):
    """ A block for publishing to a local nio communication channel.

    Functions regardless of communication module implementation.

    Unlike the regular Publisher block, the one does not need data to be json
    """
    version = VersionProperty("1.1.1")
    topic = StringProperty(title="Topic", default="")
    local_identifier = StringProperty(
        title='Local Identifier', default='[[INSTANCE_ID]]', advanced=True)

    def __init__(self):
        super().__init__()
        self._publisher = None

    def configure(self, context):
        super().configure(context)
        topic = self.topic()
        # If a local identifier was included use it as a prefix
        if self.local_identifier():
            topic = "{}.{}".format(self.local_identifier(), topic)
        self._publisher = NioPublisher(topic=topic)

        try:
            self._publisher.open(on_connected=self.conn_on_connected,
                                 on_disconnected=self.conn_on_disconnected)
        except TypeError as e:
            self.logger.warning(
                "Connecting to an outdated communication module")
            # try previous interface
            self._publisher.open()
            # no need to configure connectivity if not supported
            return

        self.conn_configure(self._publisher.is_connected)

    def stop(self):
        """ Stop the block by closing the underlying publisher """
        self._publisher.close()
        super().stop()

    def process_signals(self, signals):
        """ Publish each list of signals """
        try:
            signals = pickle.dumps(signals)
            signals = [Signal({"signals": b64encode(signals)})]
            self._publisher.send(signals)
        except pickle.PicklingError:
            self.logger.exception("Pickling based pickle error")
        except TypeError:
            self.logger.exception("Unable to encode pickled signals")
        except PublisherError:
            self.logger.exception("Error publishing signals")
        except:
            self.logger.exception("Error processing signals")

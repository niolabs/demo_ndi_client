from nio import TerminatorBlock, Block
from nio.modules.communication.publisher import Publisher as NioPublisher
from nio.modules.communication.publisher import PublisherError
from nio.properties import StringProperty, VersionProperty

from .connectivity import PubSubConnectivity


class Publisher(PubSubConnectivity, TerminatorBlock):
    """ A block for publishing to a nio communication channel.

    Functions regardless of communication module implementation.

    Properties:
        topic (str): Defines topic to use to publish signals.

    """
    version = VersionProperty("1.1.1")
    topic = StringProperty(title="Topic", default="")

    def __init__(self):
        super().__init__()
        self._publisher = None

    def configure(self, context):
        super().configure(context)
        self._publisher = NioPublisher(topic=self.topic())

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
            self._publisher.send(signals)
        except PublisherError:  # pragma no cover
            self.logger.exception("Error publishing signals")

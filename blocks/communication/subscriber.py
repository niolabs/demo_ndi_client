from nio import GeneratorBlock
from nio.modules.communication.subscriber import Subscriber as NioSubscriber
from nio.properties import StringProperty, VersionProperty

from .connectivity import PubSubConnectivity


class Subscriber(PubSubConnectivity, GeneratorBlock):
    """ A block for subscribing to a nio communication channel.

    Functions regardless of communication module implementation.

    Properties:
        topic (str): Defines topic to subscribe to in order to receive signals.

    """
    version = VersionProperty("1.1.1")
    topic = StringProperty(title="Topic", default="")

    def __init__(self):
        super().__init__()
        self._subscriber = None

    def configure(self, context):
        super().configure(context)
        self._subscriber = NioSubscriber(self._subscriber_handler,
                                         topic=self.topic())

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
        self.notify_signals(signals)

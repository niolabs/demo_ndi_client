from nio import GeneratorBlock
from nio.modules.communication.subscriber import Subscriber as NioSubscriber
from nio.properties import StringProperty, VersionProperty


class Subscriber(GeneratorBlock):
    """ A block for subscribing to a nio communication channel.

    Functions regardless of communication module implementation.

    Properties:
        topic (str): Defines topic to subscribe to in order to receive signals.

    """
    version = VersionProperty('1.0.1')
    topic = StringProperty(title='Topic')

    def __init__(self):
        super().__init__()
        self._subscriber = None

    def configure(self, context):
        super().configure(context)
        self._subscriber = NioSubscriber(self._subscriber_handler,
                                         topic=self.topic())

    def start(self):
        """ Start the block by opening the underlying subscriber """
        super().start()
        self._subscriber.open()

    def stop(self):
        """ Stop the block by closing the underlying subscriber """
        self._subscriber.close()
        super().stop()

    def _subscriber_handler(self, signals):
        self.notify_signals(signals)

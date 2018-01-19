from nio import TerminatorBlock
from nio.modules.communication.publisher import Publisher as NioPublisher
from nio.modules.communication.publisher import PublisherError
from nio.properties import StringProperty, VersionProperty


class Publisher(TerminatorBlock):
    """ A block for publishing to a nio communication channel.

    Functions regardless of communication module implementation.

    Properties:
        topic (str): Defines topic to use to publish signals.

    """
    version = VersionProperty('1.0.0')
    topic = StringProperty(title='Topic')

    def __init__(self):
        super().__init__()
        self._publisher = None

    def configure(self, context):
        super().configure(context)
        self._publisher = NioPublisher(topic=self.topic())
        self._publisher.open()

    def stop(self):
        """ Stop the block by closing the underlying publisher """
        self._publisher.close()
        super().stop()

    def process_signals(self, signals):
        """ Publish each list of signals """
        try:
            self._publisher.send(signals)
        except PublisherError:
            self.logger.exception("Error publishing signals")

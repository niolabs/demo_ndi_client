from base64 import b64decode
import pickle

from nio import GeneratorBlock
from nio.modules.communication.subscriber import Subscriber as NioSubscriber
from nio.properties import StringProperty, VersionProperty


class LocalSubscriber(GeneratorBlock):
    """ A block for subscribing to a local nio communication channel.

    Functions regardless of communication module implementation.

    Unlike the regular Subscriber block, the one does not need data to be json
    """
    version = VersionProperty("0.1.1")
    topic = StringProperty(title='Topic', default="")
    local_identifier = StringProperty(
        title='Local Identifier', default='[[INSTANCE_ID]]', visible=False)

    def __init__(self):
        super().__init__()
        self._subscriber = None

    def configure(self, context):
        super().configure(context)
        self._subscriber = NioSubscriber(
            self._subscriber_handler,
            topic="{}.{}".format(self.local_identifier(), self.topic()))

    def start(self):
        """ Start the block by opening the underlying subscriber """
        super().start()
        self._subscriber.open()

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
        except TypeError:
            self.logger.exception("Unable to decode pickled signals")
        except:
            self.logger.exception("Error handling signals")
        else:
            self.notify_signals(signals)

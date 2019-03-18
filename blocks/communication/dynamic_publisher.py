from collections import defaultdict
from threading import Lock
from base64 import b64encode
import pickle

from nio import TerminatorBlock, Signal
from nio.modules.communication.publisher import Publisher
from nio.modules.communication.publisher import PublisherError
from nio.modules.scheduler import Job
from nio.properties import BoolProperty, StringProperty, TimeDeltaProperty, VersionProperty

from .connectivity import PubSubConnectivity


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret


class DynamicPublisher(PubSubConnectivity, TerminatorBlock):
    version = VersionProperty("0.2.0")
    topic = StringProperty(
        title="Topic",
        default="",
        order=0)

    ttl = TimeDeltaProperty(
        title="Time-to-live",
        advanced=True,
        order=0,
        default=dict(seconds=600))
    is_local = BoolProperty(
        advanced=True,
        default=False,
        order=1,
        title="Local Publisher?")
    local_identifier = StringProperty(
        advanced=True,
        default='[[INSTANCE_ID]]',
        order=2,
        title='Local Identifier')

    def __init__(self):
        super().__init__()
        self._cache = keydefaultdict(lambda topic: (self.__create_publisher(topic), None))
        self._cache_lock = Lock()
        self._is_local = False
        self._local_id = None

    def configure(self, context):
        super().configure(context)
        self._is_local = self.is_local()
        if self._is_local:
            self._local_id = self.local_identifier()

    def stop(self):
        with self._cache_lock:
            for topic in self._cache:
                (pub, job) = self._cache[topic]
                if job is not None:
                    job.cancel()
                pub.close()

            self._cache.clear()

    def process_signals(self, in_signals):
        """ Publish each group of signals """
        ttl = self.ttl()
        groups = defaultdict(list)

        for signal in in_signals:
            try:
                topic = self.topic(signal)
                if self._is_local and self._local_id:
                    topic = '{}.{}'.format(self._local_id, topic)
            except Exception:
                self.logger.exception('topic expression failed, ignoring signal')
                continue
            groups[topic].append(signal)

        for topic, out_signals in groups.items():
            try:
                if self._is_local:
                    out_signals = [Signal({"signals": b64encode(pickle.dumps(out_signals))})]

                self.__get_publisher(topic, ttl).send(out_signals)
            except pickle.PicklingError:
                self.logger.exception("Pickling based pickle error")
            except TypeError:
                self.logger.exception("Unable to encode pickled signals")
            except PublisherError:  # pragma no cover
                self.logger.exception('Error publishing {:n} signals to "{}"'.format(len(out_signals), topic))
            except:
                self.logger.exception("Error processing signals")

    def __close_publisher(self, topic):
        with self._cache_lock:
            self.logger.info('removing expired publisher for "{}"'.format(topic))
            pub, _ = self._cache.pop(topic)
            pub.close()

    def __create_publisher(self, topic):
        self.logger.info('creating new publisher for "{}"'.format(topic))
        publisher = Publisher(topic=topic)

        try:
            publisher.open(
                on_connected=self.conn_on_connected,
                on_disconnected=self.conn_on_disconnected)
        except TypeError as e:
            self.logger.warning(
                'Connecting to an outdated communication module')
            # try previous interface
            publisher.open()
            # no need to configure connectivity if not supported
            return publisher

        self.conn_configure(publisher.is_connected)
        return publisher

    def __get_publisher(self, topic, ttl):
        with self._cache_lock:
            publisher, prev_job = self._cache[topic]
            if prev_job is not None:
                prev_job.cancel()

            job = (Job(
                self.__close_publisher,
                ttl,
                False,
                topic,
            ) if ttl.total_seconds() >= 0 else None)

            self._cache[topic] = (publisher, job)

            return publisher

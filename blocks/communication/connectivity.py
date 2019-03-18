from threading import RLock, Event

from nio.block.base import Base as BlockBase
from nio.properties import TimeDeltaProperty
from nio.util.runner import RunnerStatus


class PubSubConnectivity(object):
    """ Adds connectivity awareness to pubsub blocks
    """
    timeout = TimeDeltaProperty(title='Connect Timeout',
                                default={'seconds': 2},
                                advanced=True)

    def __init__(self):
        super().__init__()

        # make sure it inherits from Block's root class since class assumes
        # access to notify_management_signal, status, logger, etc
        if not isinstance(self, BlockBase):
            raise ValueError(
                "PubSubConnectivity requires it's use within a Block instance")

        self._connected = None
        self._connected_lock = RLock()
        self._warning_status_set = False
        self._connected_event = Event()

    def conn_configure(self, is_connected):
        """ Sets up instance for connectivity checks

        Args:
            is_connected (callable): function to invoke to establish initial
                connectivity status
        """
        with self._connected_lock:
            connected = is_connected()
            self.logger.info("Starting in: '{}' state".format(
                "connected" if connected else "disconnected"))
            self._connected = connected

        if not connected:
            # per spec, hold the configure method hoping to get connected
            if not self._connected_event.wait(self.timeout().total_seconds()):
                self._notify_disconnection()

    def conn_on_connected(self):
        with self._connected_lock:
            # remove any possible wait for on_connected event
            self._connected_event.set()
            self._connected = True

        # if there was a warning status formerly set then reset it
        if self._warning_status_set:
            self.set_status('ok', 'Block is connected')

    def conn_on_disconnected(self):
        # ignore disconnections when stopping/stopped
        if self.status.is_set(RunnerStatus.stopping) or \
           self.status.is_set(RunnerStatus.stopped):
            return

        with self._connected_lock:
            self._connected_event.clear()
            self._connected = False
        self._notify_disconnection()

    def _notify_disconnection(self):
        with self._connected_lock:
            # double check that we are disconnected before notifying
            if not self._connected:
                self.set_status('warning', 'Block is not connected')
                self._warning_status_set = True

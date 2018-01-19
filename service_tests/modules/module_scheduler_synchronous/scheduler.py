import heapq
from collections import namedtuple
from datetime import timedelta
from threading import Event, RLock
from time import monotonic
from uuid import uuid4

from nio.modules.module import ModuleNotInitialized
from nio.util.logging import get_nio_logger
from nio.util.runner import RunnerStatus, Runner
from nio.util.threading import spawn

QueueEvent = namedtuple('Event', 'time, id, target, frequency, args, kwargs')


class SynchronousSchedulerRunner(Runner):

    def __init__(self):
        super().__init__()
        self._sched_min_delta = 0.1
        self._sched_resolution = 0.1
        self.logger = get_nio_logger("Custom Scheduler")
        self._queue = []
        self._queue_lock = RLock()
        self._stop_event = Event()
        self._events = dict()
        self._events_lock = RLock()
        self._process_events_thread = None
        self.offset = 0
        # event used to wait for next task to execute and/or wait at scheduler
        # resolution
        self._sleep_interrupt_event = Event()

    def configure(self, context):
        # Load in the minimum delta and resolution from the config
        self._reset_scheduler()
        self._sched_min_delta = context.min_interval
        self._sched_resolution = context.resolution

    def _reset_scheduler(self):
        """ Reset the scheduler to the basic state.

        This method will be called whenever the scheduler needs to be
        restarted or start fresh. It will clear out the queue, reset the
        stop event, etc.
        """
        self._queue[:] = []
        # Set and then clear the event to trigger any needed stops
        self._stop_event.set()
        self._stop_event.clear()
        self._events.clear()
        if self._process_events_thread is not None:
            self._process_events_thread.join(self._sched_resolution)
        self.offset = 0

    def schedule_task(self, target, delta, repeatable, *args, **kwargs):
        """ Add the given task to the Scheduler.

        Args:
            target (callable): The task to be scheduled.
            delta (timedelta): The scheduling interval. The scheduler will
                wait for this interval before running 'target' for the first
                time.
            repeatable (bool): When False, 'target' is run only once.
                Otherwise, it is run repeatedly at an interval defined by
                'delta'.
            args: Positional arguments to be passed to 'target'.
            kwargs: Keyword arguments to be passed to 'target'.

        Returns:
            job (Job): The Job object.

        """
        if self.status != RunnerStatus.started:
            raise ModuleNotInitialized("Scheduler module is not started")

        if not isinstance(delta, timedelta):
            raise AttributeError('delta must be of type: timedelta')

        delta = delta.total_seconds()
        if repeatable:
            # make sure delta is not smaller than minimum
            if delta < self._sched_min_delta:
                self.logger.warning(
                    "Scheduler delta of {} is invalid, minimum is {}".format(
                        delta, self._sched_min_delta))
                delta = self._sched_min_delta
            frequency = delta
        else:
            # when non repeatable, allow delta to be as small as user wishes
            # it to be
            frequency = 0

        event_id = uuid4().hex
        event = QueueEvent(
            self._get_time() + delta, event_id, target,
            frequency, args, kwargs)

        # add to queue
        with self._queue_lock:
            heapq.heappush(self._queue, event)

        # add to events
        with self._events_lock:
            self._events[event_id] = event

        return event_id

    def unschedule(self, job):
        """Remove a job from the scheduler.

        If the given job is not currently scheduled, this method
        has no effect.

        Args:
            job: The ID of the job to remove

        Returns:
            None

        """
        self.logger.debug("Un-scheduling %s" % job)
        # remove it from events dictionary
        event = None
        with self._events_lock:
            if job in self._events:
                event = self._events.pop(job)
        if event:
            try:
                with self._queue_lock:
                    if event in self._queue:
                        self._queue.remove(event)
                        heapq.heapify(self._queue)
                self.logger.debug('Success cancelling event')
                return True
            except Exception:
                self.logger.debug('Failure to remove event {0} from queue'
                                  ' while cancelling a job'.format(event))
        return False

    def stop(self):
        self._stop_event.set()
        # do not join indefinitely, allow a reasonable time
        self._process_events_thread.join(10 * self._sched_resolution)
        if self._process_events_thread.is_alive():
            self.logger.warning("Scheduler thread did not end properly, "
                                "it timed out")

    def start(self):
        self._process_events_thread = spawn(self._process_events)

    def _process_events(self):
        """ Process scheduled events

        Starts a loop that runs indefinitely until stop_event is set.
        Uses recommended-time returned from _execute_pending_tasks to wait
            for next pending tasks execution
        Any exception that may arise is logged while loop continues execution
        """

        while not self._stop_event.is_set():
            try:
                next_try_time = self._execute_pending_tasks()
                self._sleep_interrupt_event.wait(next_try_time)
            except Exception:
                # log any exception, do not leave loop
                self.logger.exception('Exception caught')

    def _execute_pending_tasks(self):
        """ Executes pending tasks

        This method will execute pending tasks, as soon as no task is ready for
        execution it will return.

        General characteristics:
            Scheduler tasks are launched asynchronously
            When not a single event is scheduled, method will return the
            resolution time, however, when events are present the next wait
            time is calculated as the minimum between scheduler's resolution
            and next event scheduled time.

        Returns:
            recommended time to wait before events are next considered
        """
        while not self._stop_event.is_set():
            with self._queue_lock:
                # is queue empty?
                if not self._queue:
                    # amount of time recommended to wait before trying again
                    return self._sched_resolution
                # have access to first event in queue
                event = heapq.heappop(self._queue)

            # check event's time to see if it is up for execution.
            event_time, event_id, target, frequency, args, kwargs = event
            # get time to compare event against
            now = self._get_time()
            if now < event_time:
                # event is in the future so push it back and recommend time
                # to wait before trying again
                with self._queue_lock:
                    heapq.heappush(self._queue, event)
                return min(event_time - now, self._sched_resolution)
            else:
                # time is up, execute
                try:
                    self.logger.debug("Executing: {0}".format(target))
                    # launch target task from a different thread thus
                    # making scheduler independent from task duration
                    target(*args, **kwargs)
                except Exception:
                    self.logger.exception('Calling: {0}'.format(target))

                with self._events_lock:
                    # before processing any further, make sure event has
                    # not been cancelled
                    if event_id in self._events:
                        # is it repeatable?
                        if frequency:
                            # reschedule it back, adding frequency to
                            # event time
                            event = QueueEvent(event_time + frequency,
                                               event_id,
                                               target,
                                               frequency,
                                               args, kwargs)
                            # housekeeping new event in
                            with self._queue_lock:
                                heapq.heappush(self._queue, event)
                            self._events[event_id] = event
                        else:
                            # remove event when not repeatable
                            del self._events[event_id]
                    else:
                        self.logger.debug("Event: {0} was cancelled".
                                          format(event_id))

    def jump_ahead(self, seconds):
        """ Simulate a jump forward in time

        This will update the scheduler's offset a certain number of seconds
        in order to simulate time passing. Any scheduled jobs that should have
        fired during the time that passed will fire after scheduler thread
        takes control.

        Note: To facilitate the scheduler event processing thread to take
        control a 'sleep' call is invoked at the end of this method to
        avoid having to follow up with a 'sleep' call every time this method
        is invoked.

        Args:
            seconds (float): How many seconds to simulate passing in time.

        Raises:
            ValueError: If seconds is negative - can't go back in time
        """
        if float(seconds) < 0:
            raise ValueError("Cannot jump backwards in time")

        self.offset += seconds

        # have scheduler execute tasks that might be ready after this jump
        self._execute_pending_tasks()

    def _get_time(self):
        """ Time retrieval method to use when comparing against event time
        """
        # Use a clock that cannot go backwards.
        # This clock is not affected by system clock updates
        return monotonic() + self.offset

# Singleton reference to a scheduler
SyncScheduler = SynchronousSchedulerRunner()

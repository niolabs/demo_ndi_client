from datetime import datetime, timedelta

from nio.properties import StringProperty, ObjectProperty, PropertyHolder
from nio.modules.scheduler import Job
from nio.util.threading import spawn


class CronConf(PropertyHolder):
    minute = StringProperty(title='Minute', default='0')
    hour = StringProperty(title='Hour', default='0')
    day_of_month = StringProperty(title='Day of Month', default='*')
    month = StringProperty(title='Month', default='*')
    day_of_week = StringProperty(title='Day of Week', default='*')


class CronTrigger():

    """ Notify signals according to cron-like timetable """

    cron = ObjectProperty(CronConf, title='Cron Schedule', default=CronConf())

    def __init__(self):
        super().__init__()
        self._job = None
        self._cron_specs = None

    def configure(self, context):
        super().configure(context)
        # TODO: check that the config is valid cron syntax
        self._cron_specs = [self.cron().minute(),
                            self.cron().hour(),
                            self.cron().day_of_month(),
                            self.cron().month(),
                            self.cron().day_of_week()]

    def start(self):
        super().start()
        # Like crontab, check to run jobs every minute
        self._job = Job(self._cron, timedelta(minutes=1), True)
        # Run a cron cycle immediately, but in a new thread since it
        # might take some time and we don't want it to hold up start
        spawn(self._cron)

    def stop(self):
        """ Stop the simulator thread and signal generation """
        if self._job:
            self._job.cancel()
        super().stop()

    def _cron(self):
        """ Called every minute to check if cron job should notify signals """
        self.logger.debug("Checking if cron emit should run")
        now = datetime.utcnow()
        now = [str(now.minute),
               str(now.hour),
               str(now.day),
               str(now.month),
               str(now.weekday())]
        if self._check_cron(now):
            spawn(self._emit)

    def _check_cron(self, now):
        """ Return True if cron property matches with `now`

        `now` is list containing the 5 cron field
        """
        for i in range(5):
            # '*' should match no matter what
            if self._cron_specs[i] == '*':
                now[i] = '*'
        # TODO: handle more interesting cron settings than just numbers and '*'
        return now == self._cron_specs

    def _emit(self):
        self.logger.debug("Generating signals")
        signals = self.generate_signals()
        # If a generator is returned, build the list
        if not isinstance(signals, list):
            signals = list(signals)
        if signals:
            self.logger.debug("Notifying {} signals".format(len(signals)))
            self.notify_signals(signals)
        else:
            self.logger.debug("No signals generated")

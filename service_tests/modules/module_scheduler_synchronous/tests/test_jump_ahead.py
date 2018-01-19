from datetime import timedelta

from nio.testing.test_case import NIOTestCase
from nio.testing.modules.scheduler.job import JumpAheadJob
from nio.testing.modules.scheduler.scheduler import JumpAheadScheduler
from nio.testing.modules.scheduler.module import TestingSchedulerModule


class TestJumpAheadJobs(NIOTestCase):

    def setUp(self):
        super().setUp()
        self.times_called = 0

    def _callback(self):
        self.times_called += 1

    def get_test_modules(self):
        """ Returns set of modules to load during test

        Override this method to customize which modules you want to load
        during a test
        """
        return {'scheduler'}

    def get_module(self, module_name):
        if module_name == 'scheduler':
            return TestingSchedulerModule()

    def test_jump_ahead(self):
        """ Tests that we can jump ahead in time """
        job = JumpAheadJob(self._callback, timedelta(seconds=5), False)
        # Starts off not called
        self.assertEqual(self.times_called, 0)

        # After 2 seconds, still not called
        job.jump_ahead(2)
        self.assertEqual(self.times_called, 0)

        # After 4 more seconds (6 total), should be called once
        job.jump_ahead(4)
        self.assertEqual(self.times_called, 1)

    def test_schedule_new_job_after_jump_ahead(self):
        """ Jobs scheduled after a jump ahead are scheduled appropriately """
        # Start off by jumping ahead
        JumpAheadScheduler.jump_ahead(2)
        job = JumpAheadJob(self._callback, timedelta(seconds=5), False)
        self.assertEqual(self.times_called, 0)

        # After 4 more seconds, should not be called
        JumpAheadScheduler.jump_ahead(4)
        self.assertEqual(self.times_called, 0)

        # After 4 more seconds (8 total), should be called once
        JumpAheadScheduler.jump_ahead(4)
        self.assertEqual(self.times_called, 1)

    def test_jump_repeatable(self):
        """ Tests that if we jump after multiple repeats all are called.

        If we jump ahead and multiple executions were expected, all of those
        executions should be called still.
        """
        # Execute the callback every 5 seconds
        job = JumpAheadJob(self._callback, timedelta(seconds=5), True)
        # Starts off not called
        self.assertEqual(self.times_called, 0)

        # After 6 seconds, called once
        job.jump_ahead(6)
        self.assertEqual(self.times_called, 1)

        # After 15 more seconds (21 total), should be called 4 times
        job.jump_ahead(15)
        self.assertEqual(self.times_called, 4)

    def test_cant_jump_backwards(self):
        """ Make sure a ValueError is raised if we try to jump backwards """
        job = JumpAheadJob(self._callback, timedelta(seconds=5), False)
        with self.assertRaises(ValueError):
            job.jump_ahead(-5)

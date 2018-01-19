import json
import jsonschema
import os
import re
import sys
from threading import Event
from unittest.mock import MagicMock

from nio.block.base import Base
from nio.block.context import BlockContext
from nio.modules.communication.publisher import Publisher
from nio.modules.communication.subscriber import Subscriber
from nio.modules.context import ModuleContext
from nio.testing.test_case import NIOTestCase
from nio.router.context import RouterContext
from nio.util.discovery import is_class_discoverable as _is_class_discoverable
from nio.util.runner import RunnerStatus
from niocore.core.loader.discover import Discover

from .router import ServiceTestRouter
from .modules.module_persistence_file.module import FilePersistenceModule
from .modules.module_persistence_file.persistence import Persistence
from .modules.module_scheduler_synchronous.module import \
    SynchronousSchedulerModule
from .modules.module_scheduler_synchronous.scheduler import SyncScheduler

Persistence.save = MagicMock()
Persistence.save_collection = MagicMock()


def is_class_discoverable(_class, default_discoverability=True):
    return _is_class_discoverable(_class, default_discoverability)


class NioServiceTestCase(NIOTestCase):
    """Base test case for n.io services

    To use:
        * Override class variable `service_name`.
        * If testing by publishing to subscriber, override `subscriber_topics`.
            Publish this signals with `publish_signals(topic, signals)`.
        * If asserting against publised signals, override `publisher_topics`
            Get published signals with `published_signals`.
        * If you need to change block config for a test, override
            `override_block_configs`
        * Use `wait_for_published_signals(self, count=0, timeout=1)` instead
            of sleep
        * Set n.io environment variables with `env_vars`.
        * Mock blocks with `mock_blocks` by mapping block names to mocked
            process_signals method for that block.
        * Test by notifying signals from a block with `notify_signals`
    """

    service_name = None
    auto_start = True
    synchronous = True

    def __init__(self, methodName='runTests'):
        super().__init__(methodName)
        self._blocks = {}
        self._router = ServiceTestRouter(self.synchronous)
        # Set this Scheduler object to be used in tests for jump_ahead
        self._scheduler = SyncScheduler if self.synchronous else None
        # Subscribe to publishers in the service
        self._subscribers = {}
        # Capture published signals for assertions
        self.published_signals = []
        # Set an event when those publishers publish signals
        self._publisher_event = Event()
        # Allow tests to publish signals to any subscriber
        self._publishers = {}
        # Json schema for publisher and subscriber validation
        self._schema = {}

    @property
    def processed_signals(self):
        return self._router._processed_signals

    def publisher_topics(self):
        """Topics this service publishes to"""
        return []

    def subscriber_topics(self):
        """Topics this service subscribes to"""
        return []

    def publish_signals(self, topic, signals):
        """publish signals to a given topic.
        Does not add to self.published_signals
        """
        self.schema_validate(signals, topic)
        self._publishers[topic].send(signals)

    def notify_signals(self, block_name, signals,
                       terminal="__default_terminal_value"):
        """notify signals from a block. Adds to a blocks processed signals,
        but does not call block.process_signals.
        """
        self._router.notify_signals(
            self._blocks[block_name], signals, terminal)

    def mock_blocks(self):
        """Optionally create a mocked block class instead of the real thing
        Return:
            dict(block_name, process_signals): map blocks to the method to be
                called when that block's process_signals is called.
        """
        return {}

    def override_block_configs(self):
        """Optionally override block config for the tests"""
        return {}

    def env_vars(self):
        """Optionally override to set environment variable values"""
        return {}

    def setUp(self):
        super().setUp()
        self._invalid_topics = {}
        persistence = Persistence()
        self.block_configs = persistence.load_collection("blocks")
        self.service_configs = persistence.load_collection("services")
        self.service_config = self.service_configs.get(self.service_name, {})
        self._setup_blocks()
        self._setup_pubsub()
        self._setup_json_schema()
        # Start blocks
        if self.auto_start:
            self.start()

    def get_test_modules(self):
        return {'settings', 'scheduler', 'persistence', 'communication'}

    def get_context(self, module_name, module):
        if module_name == "persistence":
            context = ModuleContext()
            context.root_folder = "{}/../{}".format(
                os.path.dirname(
                    sys.modules[self.__class__.__module__].__file__),
                "etc")
            context.root_id = ''
            context.format = Persistence.Format.json.value
            return context
        else:
            return super().get_context(module_name, module)

    def get_module(self, module_name):
        """ Override to use the file persistence and scheduler """
        if module_name == "persistence":
            return FilePersistenceModule()
        if module_name == "scheduler" and self.synchronous:
            return SynchronousSchedulerModule()
        else:
            return super().get_module(module_name)

    def _setup_blocks(self):
        # Instantiate and configure blocks
        blocks = Discover.discover_classes('blocks', Base, is_class_discoverable)
        service_block_names = [service_block["name"] for service_block in
                               self.service_config.get("execution", [])]
        service_block_mappings = {}
        for mapping in self.service_config.get("mappings", []):
            service_block_mappings[mapping["name"]] = mapping["mapping"]
        for service_block_name in service_block_names:
            # get mapping name or leave original name
            mapping_name = service_block_mappings.get(service_block_name,
                                                      service_block_name)
            block_config = self.block_configs.get(mapping_name)
            if not block_config:
                # skip blocks that don't have a config - this is a problem
                print('Could not get a config for block: {}, skipping.'
                      .format(service_block_name))
                continue
            # use mapping name for block
            block_config["name"] = service_block_name
            # instantiate the block
            block = self._init_block(block_config, blocks)
            block_config = self._override_block_config(block_config)
            block_config = self._replace_env_vars(block_config)
            block.configure(BlockContext(
                self._router, block_config, 'TestSuite', ''))
            self._blocks[service_block_name] = block
        # Configure router
        self._router.configure(RouterContext(
            execution=self.service_config.get("execution", []),
            blocks=self._blocks))

    def start(self):
        # Start blocks
        if self._router.status != RunnerStatus.started:
            self._router.status = RunnerStatus.starting
            for block in self._blocks:
                self._blocks[block].start()
            self._router.status = RunnerStatus.started
        else:
            print('Already started this service, cannot start again.')

    def _init_block(self, block_config, blocks):
        """create a mocked block for each block given in self.mock_blocks."""
        if block_config["name"] in self.mock_blocks():
            block = MagicMock()
            block.name.return_value = block_config["name"]
            block.process_signals.side_effect = \
                self.mock_blocks()[block_config["name"]]
        else:
            block = [block for block in blocks if
                     block.__name__ == block_config["type"]][0]()
        return block

    def _replace_env_vars(self, config):
        """Return config with environment variables swapped out"""
        for var in self.env_vars():
            config = \
                self._replace_env_var(config, var, self.env_vars()[var])
        return config

    def _replace_env_var(self, config, name, value):
        for property in config:
            if isinstance(config[property], str):
                config[property] = re.sub("\[\[" + name + "\]\]",
                                          str(value),
                                          config[property])
            elif isinstance(config[property], dict):
                self._replace_env_var(config[property], name, value)
            elif isinstance(config[property], list):
                new_list = []
                for item in config[property]:
                    if isinstance(item, str):
                        new_list.append(re.sub("\[\[" + name + "\]\]",
                                               str(value),
                                               item))
                    elif isinstance(item, dict):
                        new_list.append(
                                self._replace_env_var(item, name, value))
                config[property] = new_list
        return config

    def tearDown(self):
        # Tear down publishers and subscribers for tests
        self._teardown_pubsub()
        # Stop blocks
        for block in self._blocks:
            self._blocks[block].stop()

        # set runner status
        self._router.status = RunnerStatus.stopped

        super().tearDown()

        # fail if there were topics found invalid and the test is not already
        # failing
        if self._invalid_topics and not self._outcome.errors:
            raise AssertionError(self._invalid_topics)

    def _setup_pubsub(self):
        # Supscribe to published signals
        for publisher_topic in self.publisher_topics():
            self._subscribers[publisher_topic] = \
                    Subscriber(self._published_signals, topic=publisher_topic)
        for subscriber in self._subscribers:
            self._subscribers[subscriber].open()
        # Allow tests to publish to subscribers in service
        for subscriber_topic in self.subscriber_topics():
            self._publishers[subscriber_topic] = \
                    Publisher(topic=subscriber_topic)
        for publisher in self._publishers:
            self._publishers[publisher].open()

    def _teardown_pubsub(self):
        self.published_signals = []
        for subscriber in self._subscribers:
            self._subscribers[subscriber].close()
        for publisher in self._publishers:
            self._publishers[publisher].close()
        self._publisher_event = Event()

    def _published_signals(self, signals, topic=None):
        # Save published signals for assertions
        self.schema_validate(signals, topic)
        self.published_signals.extend(signals)
        self._publisher_event.set()
        self._publisher_event.clear()

    def _override_block_config(self, block_config):
        """override a blocks config with the given block config"""
        new_block_config = self.override_block_configs().get(
            block_config["name"], block_config)
        for property in new_block_config:
            block_config[property] = new_block_config[property]
        return block_config

    def wait_for_processed_signals(
            self, block_name, count=0, timeout=1, input_id=None):
        """ Wait the given timeout for the given block's number of processed
        signals to be equal to count.
        """
        if not count:
            self._blocks[block_name]._processed_event.wait(timeout)
        else:
            if input_id is not None:
                signal_list = \
                    self._router.processed_signals_input[block_name][input_id]
            else:
                signal_list = self._router._processed_signals[block_name]
            while count > len(signal_list):
                if not self._blocks[block_name]._processed_event.wait(timeout):
                    return

    def wait_for_published_signals(self, count=0, timeout=1):
        """Wait for the specified number of signals to be published

        If no count is specified, then wait for the next signals to be
        published. If no signals are published before the timeout, then fail
        the test.

        Either returns after successfully waiting or fails an assertion
        """
        if not count:
            # Wait for next publisher event
            self._publisher_event.wait(timeout)
        else:
            # Wait for specified number of signals
            while count > len(self.published_signals):
                if not self._publisher_event.wait(timeout):
                    return

    def command_block(self, block_name, command_name, **kwargs):
        """call a specified blocks command with given keyword arguments"""
        try:
            command = getattr(self._blocks[block_name], command_name)
        except Exception as e:
            raise AssertionError('Could not get block command: {}. Commands '
                                 'for this block: {}'.format(command_name,
                                 list(self._blocks[block_name].get_commands().keys())),
                                 e)
        else:
            command(**kwargs)

    def _setup_json_schema(self):
        """Load the json schema file that specifies which publisher/subscriber
        topics receive which kind of data. First look in tests/ in project
        root, then look in the same directory as service_tests/, which should
        be project root. then one more directory up to system root, stopping at
        the first topic_schema.json found.
        """
        file_name = "topic_schema.json"
        file_paths = [os.path.abspath(
                         os.path.join(__file__, "../../", file_name)),
                      os.path.abspath(
                         os.path.join(__file__, "../../", "tests", file_name)),
                      os.path.abspath(
                         os.path.join(__file__, "../../../", file_name))]
        for file_path in file_paths:
            if os.path.isfile(file_path):
                with open(file_path, 'r') as json_file:
                    try:
                        self._schema = json.load(json_file)
                    except Exception as e:
                        self.fail(
                            "Problem parsing topic validation file located at "
                            "{}: {}".format(file_path, e))
                    break
        else:
            print('Could not find a topic schema file. If you wish to '
                  'do publisher/subscriber topic validation, put a '
                  '"topic_schema.json" file at {}, {}, or {}.'
                  .format(file_paths[0], file_paths[1], file_paths[2]))

        # replace env vars for schema topics
        if self._schema:
            self._schema = {self._replace_env_vars({'topic': topic})['topic']:
                            self._schema[topic] for topic in self._schema}

    def schema_validate(self, signals, topic=None):
        """validate each signal in a list against the given json schema.
        Update any error information to be collected at the end of the test."""
        if topic in self._schema:
            for signal in signals:
                try:
                    jsonschema.validate(signal.to_dict(), self._schema[topic])
                except Exception as e:
                    print("Topic {} received an invalid signal: {}"
                          .format(topic, signal))

                    self._invalid_topics.update(
                        {topic: " ".join(str(e).replace("\n", " ").split())}
                    )

    def assert_num_signals_published(self, expected):
        """asserts that the amount of published signals is equal to expected"""
        if not isinstance(expected, int):
            raise TypeError('Amount of published signals can only be an int. '
                            'Got type {}: {}'.format(type(expected), expected))
        actual = len(self.published_signals)
        if not actual == expected:
            raise AssertionError('Amount of published signals not equal to {}.'
                                 ' Actual: {}'.format(expected, actual))

    def assert_num_signals_processed(
            self, expected, block_name, input_id=None):
        """asserts on a per-block basis that the number of signals that have
        been processed is equal to expected.
        """
        if not isinstance(expected, int):
            raise TypeError('Amount of processed signals can only be an int. '
                            'Got type {}: {}'.format(type(expected), expected))

        if input_id is not None:
            actual = \
                len(self._router.processed_signals_input[block_name][input_id])
        else:
            actual = len(self.processed_signals[block_name])
        if not actual == expected:
            raise AssertionError('Amount of processed signals not equal to {}.'
                                 ' Actual: {}'.format(expected, actual))

    def assert_signal_published(self, signal_dict):
        """asserts signal_dict is in the list of published signals"""
        for published_signal in self.published_signals:
            try:
                self.assertDictEqual(published_signal.to_dict(), signal_dict)
                return
            except:
                # Check next signal
                continue
        self.fail("Signal has not been published: {}".format(signal_dict))

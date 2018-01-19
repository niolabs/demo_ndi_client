from collections import defaultdict
from copy import copy, deepcopy
from threading import Event

from nio.router.base import BlockRouter
from nio.util.threading import spawn


class ServiceTestRouter(BlockRouter):

    def __init__(self, synchronous):
        super().__init__()
        self._execution = []
        self._synchronous = synchronous
        self._blocks = {}
        self._processed_signals = defaultdict(list)
        self.processed_signals_input = \
            defaultdict(lambda: defaultdict(list))

    def configure(self, context):
        self._execution = context.execution
        self._blocks = context.blocks
        self._setup_processed()

    def notify_signals(self, block, signals, output_id):
        if not signals:
            print("Block {} notified an empty signal list".format(block))
            return
        from_block_name = block.name()
        all_receivers = [block["receivers"] for block in self._execution
                         if block["name"] == from_block_name][0]
        if not all_receivers:
            return
        # If output_id isn't in receivers, then use default output
        receivers = all_receivers.get(
            output_id, all_receivers.get("__default_terminal_value", []))
        for receiver in receivers:
            receiver_name = receiver["name"]
            input_id = receiver["input"]
            to_block = self._blocks[receiver_name]
            print("{} -> {}".format(from_block_name, receiver_name))
            try:
                cloned_signals = deepcopy(signals)
            except:
                cloned_signals = copy(signals)
            if input_id == "__default_terminal_value":
                # don't include input_id if it's default terminal
                if self._synchronous:
                    to_block.process_signals(cloned_signals)
                else:
                    spawn(to_block.process_signals, cloned_signals)
            else:
                if self._synchronous:
                    to_block.process_signals(cloned_signals, input_id)
                else:
                    spawn(to_block.process_signals, cloned_signals, input_id)

    def _processed_signals_set(self, block_name):
        self._blocks[block_name]._processed_event.set()
        self._blocks[block_name]._processed_event.clear()

    def _call_processed(self, process_signals, block_name):
        """function wrapper for calling a block's _processed_signals after
        its process_signals.
        """
        def process_wrapper(*args, **kwargs):
            try:
                input_id = args[1] if len(args) > 1 else None
                process_signals(*args, **kwargs)
            except Exception as e:
                print("Exception in block {}: {}".format(block_name, e))
            self._processed_signals[block_name].extend(args[0])
            self.processed_signals_input[block_name][input_id].extend(args[0])
            self._processed_signals_set(block_name)
        return process_wrapper

    def _setup_processed(self):
        """wrap every block's (including mocked blocks) process_signals
        function with a custom one that calls _processed_signals upon exit.

        Also give every block it's own event for processed_signals.
        """
        for block_name, block in self._blocks.items():
            block.process_signals = self._call_processed(block.process_signals,
                                                         block_name)
            block._processed_event = Event()

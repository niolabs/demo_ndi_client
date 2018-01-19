from nio import Block
from nio.util.discovery import not_discoverable
from nio.testing.block_test_case import NIOBlockTestCase

from ...multiple import MultipleSignals
from ...generators.counter import CounterGenerator


@not_discoverable
class SampleCounterBlock(CounterGenerator, Block):
    pass


@not_discoverable
class SampleCounterMultipleBlock(MultipleSignals, CounterGenerator, Block):
    pass


def get_values(signals):
    return [s.attr for s in signals]


class TestCounter(NIOBlockTestCase):

    def test_counts(self):
        counter = SampleCounterBlock()
        self.configure_block(counter, {
            'attr_name': 'attr',
            'attr_value': {
                'start': 10,
                'end': 19,
                'step': 5
            }
        })
        results = list(counter.generate_signals(3))

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].attr, 10)
        self.assertEqual(results[1].attr, 15)
        # third one should have rolled over and started over at 10
        self.assertEqual(results[2].attr, 10)

    def test_batch_counts(self):
        counter = SampleCounterBlock()
        self.configure_block(counter, {
            'attr_name': 'attr',
            'attr_value': {
                'start': 0,
                'end': 2,
                'step': 1
            }
        })
        results = get_values(counter.generate_signals(5))

        self.assertEqual(len(results), 5)
        self.assertEqual(results, [0, 1, 2, 0, 1])
        results = get_values(counter.generate_signals(5))
        self.assertEqual(results, [2, 0, 1, 2, 0])
        results = get_values(counter.generate_signals(4))
        self.assertEqual(results, [1, 2, 0, 1])
        results = get_values(counter.generate_signals(5))
        self.assertEqual(results, [2, 0, 1, 2, 0])

    def test_multiple_counts(self):
        counter = SampleCounterMultipleBlock()
        self.configure_block(counter, {
            'attr_name': 'attr',
            'attr_value': {
                'start': 10,
                'end': 19,
                'step': 5
            },
            'num_signals': 2
        })
        # Don't call generate_signals with any arguments,
        # this is likely what the trigger will do and we want the
        # mix-in to specifiy how many signals to generate
        results = list(counter.generate_signals())

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].attr, 10)
        self.assertEqual(results[1].attr, 15)

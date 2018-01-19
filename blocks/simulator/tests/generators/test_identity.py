from nio import Block
from nio.util.discovery import not_discoverable
from nio.testing.block_test_case import NIOBlockTestCase

from ...multiple import MultipleSignals
from ...generators.identity import IdentityGenerator


@not_discoverable
class SampleIdentityBlock(IdentityGenerator, Block):
    pass


@not_discoverable
class SampleIdentityMultipleBlock(MultipleSignals, IdentityGenerator, Block):
    pass


class TestIdentity(NIOBlockTestCase):

    def test_counts(self):
        identity = SampleIdentityBlock()
        results = list(identity.generate_signals(3))

        self.assertEqual(len(results), 3)

    def test_multiple_counts(self):
        identity = SampleIdentityMultipleBlock()
        self.configure_block(identity, {
            'num_signals': 2
        })
        # Don't call generate_signals with any arguments,
        # this is likely what the trigger will do and we want the
        # mix-in to specifiy how many signals to generate
        results = list(identity.generate_signals())

        self.assertEqual(len(results), 2)

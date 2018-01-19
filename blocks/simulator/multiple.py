from nio.properties import IntProperty


class MultipleSignals():

    """ Allows a Simulator to notify multiple signals at a time.

    Inherit from this mix-in before your generators and triggers inside
    your simulator block.
    """

    num_signals = IntProperty(title='Number of Signals', default=1)

    def generate_signals(self, n=None):
        # If our trigger has explicitly defined how many signals to notify,
        # then we don't want to override that here - they probably have a
        # good reason for doing so
        if n is None:
            n = self.num_signals()

        return super().generate_signals(n)

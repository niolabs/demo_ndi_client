from enum import Enum

from nio import Block
from nio.block import output
from nio.properties import (ListProperty, SelectProperty, Property,
                            PropertyHolder, VersionProperty)


class BooleanOperator(Enum):
    ANY = 0
    ALL = 1


class Condition(PropertyHolder):
    expr = Property(title='Condition')


@output('false', label='False')
@output('true', label='True')
class Filter(Block):

    """ A block for filtering signal objects based on a list of
    plaintext conditions, evaluated as Python code.

    Parameters:
        conditions (list(str)): A list of strings to be evaluated
            as filter conditions.
        operator (select): Determines whether all or any of the
            conditions must be satisfied for a signal to pass the
            filter.
    """

    version = VersionProperty(version='2.0.0', min_version='2.0.0')
    conditions = ListProperty(Condition, title='Filter Conditions', default=[])
    operator = SelectProperty(BooleanOperator, default=BooleanOperator.ALL,
                              title='Condition Operator')

    def __init__(self):
        super().__init__()
        self._expressions = None

    def configure(self, context):
        super().configure(context)
        self._expressions = tuple(c.expr for c in self.conditions())

    def process_signals(self, signals):
        self.logger.debug("Ready to process {} signals".format(len(signals)))
        true_result, false_result = self._filter_signals(signals)

        self.logger.debug("Emitting {} true signals".format(
            len(true_result)))
        if len(true_result):
            self.notify_signals(true_result, 'true')

        self.logger.debug("Emitting {} false signals".format(
            len(false_result)))
        if len(false_result):
            self.notify_signals(false_result, 'false')

    def _filter_signals(self, signals):
        """ Helper function to implement the any/all filtering """
        # bring them into local variables for speed
        true_result = []
        false_result = []
        if self.operator() is BooleanOperator.ANY:
            self.logger.debug("Filtering on an ANY condition")
            # let signal in if we find one True in the output
            for sig in signals:
                for expr in self._expressions:
                    if self._eval_expr(expr, sig):
                        self.logger.debug(
                            "Short circuiting ANY on Truthy condition")
                        true_result.append(sig)
                        break
                else:
                    false_result.append(sig)
        else:
            self.logger.debug("Filtering on an ALL condition")
            # Don't let signal in if there is a single False in the output
            for sig in signals:
                for expr in self._expressions:
                    if not self._eval_expr(expr, sig):
                        self.logger.debug(
                            "Short circuiting ALL on Falsy condition")
                        false_result.append(sig)
                        break
                else:
                    true_result.append(sig)

        return true_result, false_result

    def _eval_expr(self, expr, signal):
        try:
            return expr(signal)
        except Exception:
            self.logger.exception("Filter condition evaluation failed: ")
            raise

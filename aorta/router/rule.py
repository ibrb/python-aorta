import functools
import operator

from aorta.router.criterion import Criterion
from aorta.router.criterion import NullCriterion
from aorta.router.criterion import And


class Rule(object):
    """Specifies a routing rule consisting of one or
    more :class:`Criterion` instances.
    """

    def __init__(self, destinations, criterions=None, return_to_sender=False, exclude=None):
        """Initialize a new :class:`Rule`.

        Args:
            destinations: a list of :class:`Destination`
                instances specifying where to deliver the
                event.
            criterions: a list of :class:`Criterion`
                instances.
            return_to_sender: a boolean indicating if events
                matched by this rule should also be returned
                to the sender.
            exclude: a list of destination where events matched
                by this rule may never be routed to, for example
                because security considerations.
        """
        self.destinations = tuple(destinations)
        self.criterions = functools.reduce(operator.and_, criterions or [NullCriterion()])
        self.rts = return_to_sender
        self.exclude = set(exclude or [])

    def match(self, dto):
        """Matches the event contained in the Data Transfer
        Object (DTO) against all criterions.
        """
        return self.criterions.match(dto)

    def get_destinations(self):
        """Return a tuple containing the destinations where
        the event should be routed to, and not.
        """
        return set(self.destinations), set(self.exclude)

    def add_criterion(self, element, op, value):
        """Add a new :class:`Criterion` to the :class:`Rule`.

        Args:
            element: identifies the data-element to match on.
            op: specifies the comparison operator.
            value: the value to compare against.

        Returns:
            None
        """
        self.criterions &= Criterion(element, op, value)

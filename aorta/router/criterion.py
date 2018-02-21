import functools
import operator

from aorta.router.exc import UnknownField
from aorta.router.exc import InvalidComparison


class Criterion(object):
    """Specifies a criterion that must be matched on a
    routing rule.
    """
    EQ = 'EQ'
    NE = 'NE'
    IN = 'IN'
    EX = 'EX'
    GT = 'GT'
    LT = 'LT'
    GTE = 'GTE'
    LTE = 'LTE'
    CONTAINS = 'CONTAINS'

    _matching_ops = {
        EQ: operator.eq,
        NE: operator.ne,
        IN: lambda x, y: operator.contains(y, x),
        CONTAINS: operator.contains,
        EX: lambda x, y: not operator.contains(x, y),
        GT: operator.gt,
        LT: operator.lt,
        GTE: lambda x, y: operator.gt(x, y) or operator.eq(x, y),
        LTE: lambda x, y: operator.lt(x, y) or operator.eq(x, y)
    }

    def __init__(self, attname, op, value):
        assert op in self._matching_ops, op
        self.path = attname
        self.match_func = self._matching_ops[op]
        self.op = op
        self.value = value

        # Coerce value to set if operator is IN,
        # for improved performance.
        if self.op == 'IN' and value is not None:
            self.value = set(self.value)

    def get(self, dto, attname):
        try:
            return getattr(dto, attname)
        except AttributeError:
            return dto[attname] if isinstance(dto, dict)\
                else None

    def parse_attribute(self, dto, path):
        fn = self.get

        if path.find('.') == -1:
            return fn(dto, path)

        current, descendants = path.rsplit('.', 1)
        return self.parse_attribute(fn(dto, current),
            descendants)

    def match(self, dto):
        """Matches the event contained by the Data Transfer Object
        (DTO) `dto` and returns a boolean indicating if it matches
        `this` criterion.
        """
        try:
            value = self.parse_attribute(dto, self.path)
        except (KeyError, AttributeError) as e:
            raise UnknownField(self.path)

        try:
            return self.match_func(value, self.value)
        except TypeError:
            raise InvalidComparison(value, self.op, self.value)

    def __and__(self, other):
        return And(self, other)


class NullCriterion(object):
    """A placeholder so the & operator can be supported when
    there a no :class:`Criterion` instances defined yet.
    """

    def match(self, *args, **kwargs):
        return True

    def __and__(self, other):
        return And(self, other)


class And(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def match(self, dto):
        return self.x.match(dto) and self.y.match(dto)

    def __and__(self, other):
        return And(self, other)

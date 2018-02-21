import unittest

from aorta.router.exc import UnknownField
from aorta.router.exc import InvalidComparison
from aorta.router.criterion import Criterion


class CriterionTestCase(unittest.TestCase):

    def setUp(self):
        self.dto = {
            'header': {
                'foo': 1,
                'bar': 'a',
                'baz': [1]
            }
        }

    def test_match_simple_scalar(self):
        c = Criterion('header.foo','EQ', 1)
        self.assertTrue(c.match(self.dto))

    def test_match_and_scalar(self):
        c = Criterion('header.foo','EQ', 1)
        c &= Criterion('header.foo', 'GT', 0)
        self.assertTrue(c.match(self.dto))

    def test_match_and_and_scalar(self):
        c = Criterion('header.foo','EQ', 1)
        c &= Criterion('header.foo', 'GT', 0)
        c &= Criterion('header.foo', 'LT', 4)
        self.assertTrue(c.match(self.dto))

    def test_unknown_field_raises(self):
        c = Criterion('header.blaaaaaa','EQ', 1)
        with self.assertRaises(UnknownField):
            c.match(self.dto)

    def test_invalid_comparison_raises(self):
        c = Criterion('header.foo','IN', None)
        with self.assertRaises(InvalidComparison):
            c.match(self.dto)

    def test_with_iterable(self):
        c = Criterion('header.foo', 'IN', [1,2,3])
        self.assertTrue(c.match(self.dto))

    def test_contains_true(self):
        c = Criterion('header.baz', 'CONTAINS', 1)
        self.assertTrue(c.match(self.dto))

    def test_contains_false(self):
        c = Criterion('header.baz', 'CONTAINS', 2)
        self.assertTrue(not c.match(self.dto))

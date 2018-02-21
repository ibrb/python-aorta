import unittest

from aorta.router.exc import UnknownField
from aorta.router.exc import InvalidComparison
from aorta.router import Rule


class RuleTestCase(unittest.TestCase):

    def setUp(self):
        self.dto = {
            'header': {
                'foo': 1,
                'bar': 'a',
                'baz': [1]
            }
        }
        self.rule = Rule(["foo","bar"])

    def test_match_simple_scalar(self):
        self.rule.add_criterion('header.foo','EQ', 1)
        self.assertTrue(self.rule.match(self.dto))

    def test_match_and_scalar(self):
        self.rule.add_criterion('header.foo','EQ', 1)
        self.rule.add_criterion('header.foo', 'GT', 0)
        self.assertTrue(self.rule.match(self.dto))

    def test_match_and_and_scalar(self):
        self.rule.add_criterion('header.foo','EQ', 1)
        self.rule.add_criterion('header.foo', 'GT', 0)
        self.rule.add_criterion('header.foo', 'LT', 4)
        self.assertTrue(self.rule.match(self.dto))

    def test_unknown_field_raises(self):
        self.rule.add_criterion('header.blaaaaaa','EQ', 1)
        with self.assertRaises(UnknownField):
            self.rule.match(self.dto)

    def test_invalid_comparison_raises(self):
        self.rule.add_criterion('header.foo','IN', None)
        with self.assertRaises(InvalidComparison):
            self.rule.match(self.dto)

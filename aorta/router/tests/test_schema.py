import unittest

from aorta.router.schema import CriterionSchema


class TestCriterionSchema(unittest.TestCase):

    def setUp(self):
        self.schema = CriterionSchema()

    def test_nonstrict_with_errors(self):
        params, errors = self.schema.load({'foo':'bar'})
        self.assertTrue(errors)

import unittest

import marshmallow

from aorta.router.schema import CriterionSchema


class TestCriterionSchema(unittest.TestCase):

    def setUp(self):
        self.schema = CriterionSchema()

    def test_nonstrict_with_errors(self):
        with self.assertRaises(marshmallow.exceptions.ValidationError):
            params = self.schema.load({'foo':'bar'})

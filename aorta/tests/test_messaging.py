import unittest

from aorta.const import APROP_MESSAGE_CLASS
from aorta.messaging import AortaMessage
from aorta.messaging import EventMessage


class AortaMessageTestCase(unittest.TestCase):

    def test_init_raises_assertionerror(self):
        with self.assertRaises(AssertionError):
            AortaMessage()


class EventMessageTestCase(unittest.TestCase):

    def test_init_sets_properties_to_dict(self):
        m = EventMessage()
        self.assertIsInstance(m.properties, dict)

    def test_init_sets_amc_property(self):
        m = EventMessage()
        self.assertEqual(m.properties[APROP_MESSAGE_CLASS], 'event')

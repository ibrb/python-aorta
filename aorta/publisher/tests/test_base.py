import unittest

from ...messaging import Message
from ..base import BasePublisher


class BasePublisherTestCase(unittest.TestCase):

    def setUp(self):
        self.message = Message()
        self.publisher = BasePublisher()
        self.publisher.publish(self.message)

    def random_message(self):
        return Message()

    def test_publish_flags_message_as_durable(self):
        self.assertTrue(self.message.durable)

    def test_publish_initializes_delivery_count(self):
        self.assertEqual(self.message.delivery_count, 0)

    def test_publish_sets_creation_time(self):
        m = self.random_message()
        self.publisher.publish(m)
        self.assertTrue(m.creation_time is not None)

    def test_publish_does_not_overwrite_creation_time(self):
        m = self.random_message()
        m.creation_time = 1
        self.publisher.publish(m)
        self.assertEqual(m.creation_time, 1)

    def test_publish_sets_id(self):
        m = self.random_message()
        self.publisher.publish(m)
        self.assertTrue(m.id is not None)

    def test_publish_sets_id_as_string(self):
        m = self.random_message()
        self.publisher.publish(m)
        self.assertIsInstance(m.id, str)

    def test_publish_does_not_overwrite_existing_id(self):
        m = self.random_message()
        i = m.id = 'foo'
        self.publisher.publish(m)
        self.assertEqual(m.id, i)

    def test_publish_sets_correlation_id(self):
        m = self.random_message()
        self.publisher.publish(m)
        self.assertTrue(m.correlation_id is not None)

    def test_publish_sets_correlation_id_as_string(self):
        m = self.random_message()
        self.publisher.publish(m)
        self.assertIsInstance(m.correlation_id, str)

    def test_publish_does_not_overwrite_existing_correlation_id(self):
        m = self.random_message()
        i = m.correlation_id = 'foo'
        self.publisher.publish(m)
        self.assertEqual(m.correlation_id, i)

    def test_on_settled_is_invoked(self):
        m = self.random_message()
        self.publisher.publish(m, lambda message: None)
        

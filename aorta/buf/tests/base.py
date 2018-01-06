import collections
import os
import time
import unittest
import uuid

from proton import Message

from aorta.lib import timezone


class BaseBufferImplementationTestCase(unittest.TestCase):
    """Testcase mixin that tests the behavior of :class:`BaseBuffer`
    implementations.
    """
    __test__ = False
    message_classes = (Message,)

    def setUp(self):
        self.sender = MockSender()

    def random_message(self):
        message = Message()
        message.id = uuid.UUID(bytes=os.urandom(16))
        message.correlation_id = uuid.UUID(bytes=os.urandom(16))
        message.delivery_count = 0
        message.creation_time = timezone.now()
        return message

    def test_put_increases_count_by_one(self):
        """put() results in the message count being increased."""
        n = len(self.buf)
        self.buf.put(self.random_message())
        self.assertEqual(n + 1, len(self.buf))

    def test_pop_decreases_count(self):
        """Invoking pop() must decrease the queued message count
        by one.
        """
        self.buf.put(self.random_message())
        n = len(self.buf)
        self.buf.pop()
        self.assertEqual(n - 1, len(self.buf))

    def test_pop_returns_message(self):
        """pop() must return a correct message type."""
        self.buf.put(self.random_message())
        self.assertIsInstance(self.buf.pop(), self.message_classes)

    def test_pop_does_not_return_nbf_in_future(self):
        """pop() must not return a message that has a not-before timestamp
        in the future.
        """
        self.buf.put(self.random_message(), delay=5000)
        self.assertEqual(self.buf.pop(), None)

    def test_pop_returns_message_when_nbf_expired(self):
        """pop() must return messages which have their not-before timestamp
        in the past.
        """
        self.buf.put(self.random_message(), delay=25)
        self.assertEqual(self.buf.pop(), None)

        time.sleep(0.05)
        self.assertIsInstance(self.buf.pop(), self.message_classes)

    def test_transfer_removes_one_message_from_queue(self):
        """transfer() removes one message from the queue."""
        self.buf.put(self.random_message())
        n = len(self.buf)

        self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender)
        self.assertEqual(n - 1, len(self.buf))

    def test_transfer_handles_no_message_correctly(self):
        """transfer() must gracefully handle empty queue."""
        self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender)

    def test_transfer_handles_no_message_correctly_nbf(self):
        """transfer() must gracefully handle empty queue."""
        self.buf.put(self.random_message(), delay=25)
        self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender)


Delivery = collections.namedtuple('Delivery',
    ['tag','link'])


class MockSender:
    """Mocks a :class:`proton.Sender` instance."""
    name = 'mock_link'

    def send(self, message, tag=None):
        return Delivery(tag, self)

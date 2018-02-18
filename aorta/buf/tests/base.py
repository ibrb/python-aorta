import collections
import os
import time
import unittest
import uuid

from proton import Disposition
from proton import Message

from aorta.lib import timezone


class BaseBufferImplementationTestCase(unittest.TestCase):
    """Testcase mixin that tests the behavior of :class:`BaseBuffer`
    implementations.
    """
    __test__ = False
    message_classes = (Message,)
    ACCEPTED = Disposition.ACCEPTED
    REJECTED = Disposition.REJECTED
    RELEASED = Disposition.RELEASED
    MODIFIED = Disposition.MODIFIED

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

    def test_transfer_exits_if_sender_has_no_credit(self):
        """transfer() does nothing if the sender has no credit."""
        self.sender.credit = 0
        self.buf.put(self.random_message())
        n = len(self.buf)

        t = self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender)
        self.assertEqual(t, None)

    def test_transfer_does_not_pop_queue_if_has_no_credit(self):
        """transfer() does nothing if the sender has no credit."""
        self.sender.credit = 0
        self.buf.put(self.random_message())
        n = len(self.buf)

        t = self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender)
        self.assertEqual(n, len(self.buf))

    def test_transfer_removes_one_message_from_queue(self):
        """transfer() removes one message from the queue."""
        self.buf.put(self.random_message())
        n = len(self.buf)

        self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender)
        self.assertEqual(n - 1, len(self.buf))

    def test_transfer_sets_channel(self):
        """transfer() removes one message from the queue."""
        self.buf.put(self.random_message())
        n = len(self.buf)

        tag = self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender,
            channel='foo')
        m = self.buf.get(tag)
        self.assertEqual(m.address, 'foo')

    def test_transfer_increases_deliveries(self):
        """transfer() removes one message from the queue."""
        self.buf.put(self.random_message())
        n = self.buf.deliveries

        self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender)
        self.assertEqual(n + 1, self.buf.deliveries)

    def test_transfer_handles_no_message_correctly(self):
        """transfer() must gracefully handle empty queue."""
        self.assertEqual(self.buf.queued, 0)
        self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender)

    def test_transfer_handles_no_message_correctly_nbf(self):
        """transfer() must gracefully handle empty queue."""
        self.buf.put(self.random_message(), delay=25)
        self.buf.transfer('127.0.0.1:8000', 'local', 'remote', self.sender)

    def test_on_rejected_increases_delivery_count(self):
        """The delivery count must increase when a message is rejected."""
        message = self.random_message()
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)
        count = message.delivery_count

        self.buf.on_rejected(Delivery(tag, self.sender), message,
            Disposition(False))
        self.assertEqual(message.delivery_count, count + 1)

    def test_on_rejected_increases_failed_count(self):
        """The failed count must increase when a message is rejected."""
        message = self.random_message()
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_rejected(Delivery(tag, self.sender), message,
            Disposition(False))
        self.assertEqual(self.buf.failed, 1)

    def test_on_rejected_does_not_requeue_message(self):
        """Rejected messages must not be requeued."""
        message = self.random_message()
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_rejected(Delivery(tag, self.sender), message,
            Disposition(False))
        self.assertEqual(self.buf.queued, 0)

    def test_on_release_does_not_increase_delivery_count(self):
        """The delivery count must not increase when a message is released."""
        message = self.random_message()
        count = message.delivery_count
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_released(Delivery(tag, self.sender), message,
            Disposition(False))
        self.assertEqual(message.delivery_count, count)

    def test_on_release_does_not_increase_failed_count(self):
        """The failed count must not increase when a message is released."""
        message = self.random_message()
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_released(Delivery(tag, self.sender), message,
            Disposition(False))
        self.assertEqual(self.buf.failed, 0)

    def test_on_release_requeues_message(self):
        """The failed count must not increase when a message is released."""
        message = self.random_message()
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_released(Delivery(tag, self.sender), message,
            Disposition(False))

    def test_on_modified_does_increase_delivery_count(self):
        """The delivery count must increase when a message is modified."""
        disposition = Disposition(undeliverable=False)
        message = self.random_message()
        count = message.delivery_count
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_modified(Delivery(tag, self.sender),
            message, disposition)
        self.assertEqual(message.delivery_count, count + 1)

    def test_on_modified_does_not_increase_failed_count(self):
        """The failed count must not increase when a message is modified."""
        disposition = Disposition(undeliverable=False)
        message = self.random_message()
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_modified(Delivery(tag, self.sender),
            message, disposition)
        self.assertEqual(self.buf.failed, 0)

    def test_on_modified_requeues_message(self):
        """Failed messages must be requeued."""
        disposition = Disposition(undeliverable=False)
        message = self.random_message()
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_modified(Delivery(tag, self.sender),
            message, disposition)
        self.assertEqual(self.buf.queued, 1)

    def test_on_modified_undeliverable_does_increase_delivery_count(self):
        """The delivery count must increase when a message is modified."""
        disposition = Disposition(undeliverable=True)
        message = self.random_message()
        count = message.delivery_count
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_modified(Delivery(tag, self.sender),
            message, disposition)
        self.assertEqual(message.delivery_count, count + 1)

    def test_on_modified_undeliverable_does_increase_failed_count(self):
        """The failed count must increase when a message is modified."""
        disposition = Disposition(undeliverable=True)
        message = self.random_message()
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_modified(Delivery(tag, self.sender),
            message, disposition)
        self.assertEqual(self.buf.failed, 1)

    def test_on_modified_undeliverable_does_not_requeue_message(self):
        """Undeliverable messages must not get requeued."""
        disposition = Disposition(undeliverable=True)
        message = self.random_message()
        self.buf.put(message)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.buf.on_modified(Delivery(tag, self.sender),
            message, disposition)
        self.assertEqual(self.buf.queued, 0)

    def test_on_accepted_removes_delivery(self):
        """The failed count must not increase when a message is released."""
        disposition = Disposition(undeliverable=True)
        m1 = self.random_message()
        m2 = self.random_message()
        self.buf.put(m1)
        self.buf.put(m2)

        # Transfer both messages, deliveries must be 2
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)
        self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        self.assertEqual(self.buf.deliveries, 2)
        self.buf.on_accepted(Delivery(tag, self.sender),
            self.buf.get(tag), disposition)
        self.assertEqual(self.buf.deliveries, 1)

    def test_get_by_tag_returns_correct_message(self):
        m1 = self.random_message()
        self.buf.put(m1)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)

        m2 = self.buf.get(tag)
        self.assertEqual(m1.id, m2.id)

    def test_unknown_tag_raises_lookuperror(self):
        with self.assertRaises(LookupError):
            self.buf.get('foo')

    def test_ordering_is_preserved(self):
        m1 = self.random_message()
        m2 = self.random_message()
        m3 = self.random_message()
        self.buf.put(m1)
        self.buf.put(m2)
        self.buf.put(m3)
        self.assertEqual(self.buf.pop().id, m1.id)
        self.assertEqual(self.buf.pop().id, m2.id)
        self.assertEqual(self.buf.pop().id, m3.id)

    def test_accepted_outcome(self):
        m1 = self.random_message()
        self.buf.put(m1)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)
        delivery = Delivery(tag=tag, link=self.sender)
        self.buf.on_settled(delivery, self.ACCEPTED,
            Disposition(False))

    def test_rejected_outcome(self):
        m1 = self.random_message()
        self.buf.put(m1)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)
        delivery = Delivery(tag=tag, link=self.sender)
        self.buf.on_settled(delivery, self.REJECTED,
            Disposition(False))

    def test_released_outcome(self):
        m1 = self.random_message()
        self.buf.put(m1)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)
        delivery = Delivery(tag=tag, link=self.sender)
        self.buf.on_settled(delivery, self.RELEASED,
            Disposition(False))

    def test_modified_outcome(self):
        m1 = self.random_message()
        self.buf.put(m1)
        tag = self.buf.transfer('127.0.0.1:5672', 'local','remote',
            self.sender)
        delivery = Delivery(tag=tag, link=self.sender)
        self.buf.on_settled(delivery, self.MODIFIED,
            Disposition(False))


Disposition = collections.namedtuple('Disposition', ['undeliverable'])


Delivery = collections.namedtuple('Delivery',
    ['tag','link'])


class MockSender:
    """Mocks a :class:`proton.Sender` instance."""
    name = 'mock_link'
    credit = 1

    def send(self, message, tag=None):
        return Delivery(tag, self)

import tempfile
import unittest


from ...const import P_OBJECT_TYPE
from ...const import P_EVENT_OBSERVED
from ...const import P_EVENT_OCCURRED
from .. import EventPublisher


class EventPublisherTestCase(unittest.TestCase):

    def setUp(self):
        self.publisher = EventPublisher(
            spool=tempfile.mkdtemp())
        self.buf = self.publisher.backend

    def test_publish_sets_object_type(self):
        self.publisher.publish('FooEvent', {'foo': 1})
        m = self.buf.pop()
        self.assertEqual(m.properties[P_OBJECT_TYPE], 'FooEvent')

    def test_publish_puts_message_on_buffer(self):
        params = {'foo': 1}
        self.assertEqual(len(self.buf), 0)
        self.publisher.publish('FooEvent', params)
        self.assertEqual(len(self.buf), 1)

    def test_params_is_set_as_message_body(self):
        params = {'foo': 1}
        self.publisher.publish('FooEvent', params)
        m = self.buf.pop()
        self.assertEqual(m.body, params)

    def test_event_observed_is_not_overwritten(self):
        params = {'foo': 1}
        self.publisher.publish('FooEvent', params, observed=1)
        m = self.buf.pop()
        self.assertEqual(m.properties[P_EVENT_OBSERVED], 1)

    def test_event_occurred_is_not_overwritten(self):
        params = {'foo': 1}
        self.publisher.publish('FooEvent', params, occurred=1)
        m = self.buf.pop()
        self.assertEqual(m.properties[P_EVENT_OCCURRED], 1)

    def test_event_observed_is_set_if_not_provided(self):
        params = {'foo': 1}
        self.publisher.publish('FooEvent', params)
        m = self.buf.pop()
        self.assertTrue(m.properties[P_EVENT_OBSERVED] is not None)

    def test_event_occurred_is_set_if_not_provided(self):
        params = {'foo': 1}
        self.publisher.publish('FooEvent', params)
        m = self.buf.pop()
        self.assertTrue(m.properties[P_EVENT_OCCURRED] is not None)

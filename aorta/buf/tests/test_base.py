import datetime
import unittest

from ..base import BaseBuffer


class BaseBufferTestCase(unittest.TestCase):

    def setUp(self):
        self.buf = BaseBuffer()

    def test_delay_returns_equal_datetimes_with_none_input(self):
        qat, nbf = self.buf.delay()
        self.assertEqual(qat, nbf)

    def test_delay_returns_added_datetimes(self):
        qat, nbf = self.buf.delay(300000)
        self.assertLess(qat, nbf)
        self.assertEqual(qat, nbf - datetime.timedelta(seconds=300))

    def test_pop_raises_notimplementederror(self):
        with self.assertRaises(NotImplementedError):
            self.buf.pop()

    def test_put_raises_notimplementederror(self):
        with self.assertRaises(NotImplementedError):
            self.buf.put(None)

    def test_enqueue_raises_notimplementederror(self):
        with self.assertRaises(NotImplementedError):
            self.buf.enqueue(None, None, None)

    def test_len_raises_notimplementederror(self):
        with self.assertRaises(NotImplementedError):
            len(self.buf)

    def test_track_raises_notimplementederror(self):
        with self.assertRaises(NotImplementedError):
            self.buf.track(None, None, None, None, None, None, None)

    def test_error_raises_notimplementederror(self):
        with self.assertRaises(NotImplementedError):
            self.buf.error(None, None)

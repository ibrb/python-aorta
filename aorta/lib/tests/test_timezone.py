import datetime
import unittest

from aorta.lib import timezone


class NowTestCase(unittest.TestCase):

    def test_invoke(self):
        timezone.now()

    def test_tzname(self):
        timezone.utc(0).tzname(None)


class AsDatetimeTestCase(unittest.TestCase):

    def test_raises_valueerror_with_unknown_timezone(self):
        with self.assertRaises(ValueError):
            timezone.as_datetime(0, 'foo')

    def test_with_europe_amsterdam_returns_correct(self):
        value = timezone.as_datetime(0, 'Europe/Amsterdam')
        self.assertEqual(value.hour, 1, value)


class AsTimestampTestCase(unittest.TestCase):

    def test_raises_typeerror_with_invalid_input(self):
        with self.assertRaises(TypeError):
            timezone.as_timestamp(0)

    def test_with_epoch_date(self):
        value = datetime.date(1970, 1, 1)
        self.assertEqual(timezone.as_timestamp(value), 0)

    def test_with_epoch_datetime(self):
        value = datetime.datetime(1970, 1, 1)
        self.assertEqual(timezone.as_timestamp(value), 0)

    def test_with_epoch_time(self):
        value = datetime.time(0, 0, 0)
        self.assertEqual(timezone.as_timestamp(value), 0)

    def test_with_min_time(self):
        value = datetime.time.min
        self.assertEqual(timezone.as_timestamp(value), 0)

    def test_with_max_time(self):
        value = datetime.time.max
        self.assertEqual(timezone.as_timestamp(value), 86399999)

    def test_with_epoch_datetime_aware_utc0(self):
        tz = timezone.utc(0)
        value = datetime.datetime(1970, 1, 1, tzinfo=tz)
        self.assertEqual(timezone.as_timestamp(value), 0)

    def test_with_epoch_time_aware_utc0(self):
        tz = timezone.utc(0)
        value = datetime.time(0, 0, 0, tzinfo=tz)
        self.assertEqual(timezone.as_timestamp(value), 0)

    def test_with_epoch_datetime_aware_utc1(self):
        tz = timezone.utc(3600)
        value = datetime.datetime(1970, 1, 1, tzinfo=tz)
        self.assertEqual(timezone.as_timestamp(value), 3600000)

    def test_with_epoch_time_aware_utc1(self):
        tz = timezone.utc(3600)
        value = datetime.time(0, 0, 0, tzinfo=tz)
        self.assertEqual(timezone.as_timestamp(value), 3600000)

    def test_with_epoch_datetime_aware_utc1m(self):
        tz = timezone.utc(-3600)
        value = datetime.datetime(1970, 1, 1, tzinfo=tz)
        self.assertEqual(timezone.as_timestamp(value), -3600000)

    def test_with_epoch_time_aware_utc1m(self):
        tz = timezone.utc(-3600)
        value = datetime.time(0, 0, 0, tzinfo=tz)
        self.assertEqual(timezone.as_timestamp(value), -3600000)

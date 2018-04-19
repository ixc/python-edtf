import unittest

from time import struct_time
from datetime import datetime, date

from edtf import convert


class TestConversions(unittest.TestCase):

    def test_dt_to_struct_time_for_datetime(self):
        now = datetime.now()
        st = convert.dt_to_struct_time(now)
        # Check equal year, month, day, hours, minutes, seconds
        self.assertEqual(st[:6], now.timetuple()[:6])
        # Confirm 'extra' fields are set to defaults
        self.assertEqual(st[6:], (0, 0, -1))

    def test_dt_to_struct_time_for_date(self):
        today = date.today()
        st = convert.dt_to_struct_time(today)
        # Check equal year, month, day
        self.assertEqual(st[:3], today.timetuple()[:3])
        # Confirm time fields are zeroed
        self.assertEqual(st[3:6], (0, 0, 0))
        # Confirm 'extra' fields are set to defaults
        self.assertEqual(st[6:], (0, 0, -1))

    def test_struct_time_to_date(self):
        st = struct_time(
            [2018, 4, 19] + convert.TIME_EMPTY_TIME + convert.TIME_EMPTY_EXTRAS)
        d = date(*st[:3])
        self.assertEqual(d, convert.struct_time_to_date(st))

    def test_struct_time_to_datetime(self):
        st = struct_time(
            [2018, 4, 19] + [10, 13, 54] + convert.TIME_EMPTY_EXTRAS)
        dt = datetime(*st[:6])
        converted_dt = convert.struct_time_to_datetime(st)
        self.assertEqual(dt, converted_dt)
        # Note that 'extra' fields are auto-populated by `datetime` module
        self.assertEqual(converted_dt.timetuple()[6:], (3, 109, -1))

    def test_trim_struct_time(self):
        now = datetime.now()
        st = now.timetuple()
        trimmed_st = convert.trim_struct_time(st)
        # Confirm trimmed `struct_time` has expected date/time values
        self.assertEqual(
            trimmed_st[:6],
            (now.year, now.month, now.day, now.hour, now.minute, now.second)
        )
        # Confirm 'extra' fields are set to defaults
        self.assertEqual(trimmed_st[6:], (0, 0, -1))
        # Confirm 'extra' fields in untrimmed `struct_time` has real values
        self.assertNotEqual(st[6:], (0, 0, -1))

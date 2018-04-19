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

    def test_struct_time_to_jd(self):
        # Check conversion of AD date & time to Julian Date number
        st_ad = struct_time(
            [2018, 4, 19] + [10, 13, 54] + convert.TIME_EMPTY_EXTRAS)
        jd_ad = 2458227.9263194446
        self.assertEqual(jd_ad, convert.struct_time_to_jd(st_ad))
        # Check conversion of BC date & time to Julian Date number
        st_bc = struct_time(
            [-2018, 4, 19] + [10, 13, 54] + convert.TIME_EMPTY_EXTRAS)
        jd_bc = 984091.9263194444
        self.assertEqual(jd_bc, convert.struct_time_to_jd(st_bc))

    def test_jd_to_struct_time(self):
        # Check conversion of Julian Date number to AD date & time
        jd_ad = 2458227.9263194446  # As in `test_struct_time_to_jd`
        st_ad = struct_time(
            [2018, 4, 19] + [10, 13, 54] + convert.TIME_EMPTY_EXTRAS)
        self.assertEqual(st_ad, convert.jd_to_struct_time(jd_ad))
        # Check conversion of Julian Date number to BC date & time
        # WARNING: Converted time is off by 1 second, 53 not 54
        jd_bc = 984091.9263194444  # As in `test_struct_time_to_jd`
        st_bc = struct_time(
            [-2018, 4, 19] + [10, 13, 54 - 1] + convert.TIME_EMPTY_EXTRAS)
        self.assertEqual(st_bc, convert.jd_to_struct_time(jd_bc))

    def test_jd_round_trip_for_extreme_future(self):
        original_st = struct_time(
            [999999, 8, 4] + [21, 15, 3] + convert.TIME_EMPTY_EXTRAS)
        jd = convert.struct_time_to_jd(original_st)
        converted_st = convert.jd_to_struct_time(jd)
        # Confirm that year, month, day, hour, minute are correct (not second)
        self.assertEqual(original_st[:5], converted_st[:5])
        # WARNING: Seconds are off by 1, should be 3 but is 2
        self.assertEqual(3 - 1, converted_st[5])

    def test_jd_round_trip_for_extreme_past(self):
        original_st = struct_time(
            [-999999, 8, 4] + [21, 15, 3] + convert.TIME_EMPTY_EXTRAS)
        converted_st = convert.jd_to_struct_time(
            convert.struct_time_to_jd(original_st))
        # WARNING: We have lost a year of accuracy
        self.assertEqual(
            (-999999 + 1,  # Year off by 1
             8, 4, 21, 15, 3, 0, 0, -1),
            tuple(converted_st))

    def test_jd_round_trip_for_zero_year_aka_1_bc(self):
        original_st = struct_time(
            [0, 9, 5] + [4, 58, 59] + convert.TIME_EMPTY_EXTRAS)
        converted_st = convert.jd_to_struct_time(
            convert.struct_time_to_jd(original_st))
        self.assertEqual(
            (0, 9, 5, 4, 58, 59, 0, 0, -1),
            tuple(converted_st))

    def test_jd_round_trip_for_2_bc(self):
        original_st = struct_time(
            [-1, 12, 5] + [4, 58, 59] + convert.TIME_EMPTY_EXTRAS)
        converted_st = convert.jd_to_struct_time(
            convert.struct_time_to_jd(original_st))
        self.assertEqual(
            (-1, 12, 5, 4, 58, 59, 0, 0, -1),
            tuple(converted_st))

    def test_roll_negative_time_fields(self):
        # Confirm time value is adjusted as expected
        year = -100
        month = -17  # More than 1 year
        day = -34  # More than 1 month
        hour = -25  # More than 1 day
        minute = -74  # More than 1 hour
        second = -253  # More than 1 minute
        self.assertEqual(
            (-102, 5, 24, 21, 41, 47),
            convert._roll_negative_time_fields(
                year, month, day, hour, minute, second)
        )

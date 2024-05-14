# ruff: noqa: S101 # Asserts are ok in tests

from datetime import date, datetime
from time import struct_time

from edtf import convert


def test_dt_to_struct_time_for_datetime():
    now = datetime.now()
    st = convert.dt_to_struct_time(now)
    assert st[:6] == now.timetuple()[:6]
    assert st[6:] == (0, 0, -1)


def test_dt_to_struct_time_for_date():
    today = date.today()
    st = convert.dt_to_struct_time(today)
    assert st[:3] == today.timetuple()[:3]
    assert st[3:6] == (0, 0, 0)
    assert st[6:] == (0, 0, -1)


def test_struct_time_to_date():
    st = struct_time(
        [2018, 4, 19] + convert.TIME_EMPTY_TIME + convert.TIME_EMPTY_EXTRAS
    )
    d = date(*st[:3])
    assert d == convert.struct_time_to_date(st)


def test_struct_time_to_datetime():
    st = struct_time([2018, 4, 19] + [10, 13, 54] + convert.TIME_EMPTY_EXTRAS)
    dt = datetime(*st[:6])
    converted_dt = convert.struct_time_to_datetime(st)
    assert dt == converted_dt
    assert converted_dt.timetuple()[6:] == (3, 109, -1)


def test_trim_struct_time():
    now = datetime.now()
    st = now.timetuple()
    trimmed_st = convert.trim_struct_time(st)
    assert trimmed_st[:6] == (
        now.year,
        now.month,
        now.day,
        now.hour,
        now.minute,
        now.second,
    )
    assert trimmed_st[6:] == (0, 0, -1)
    assert st[6:] != (0, 0, -1)


def test_struct_time_to_jd():
    st_ad = struct_time([2018, 4, 19] + [10, 13, 54] + convert.TIME_EMPTY_EXTRAS)
    jd_ad = 2458227.9263194446
    assert jd_ad == convert.struct_time_to_jd(st_ad)
    st_bc = struct_time([-2018, 4, 19] + [10, 13, 54] + convert.TIME_EMPTY_EXTRAS)
    jd_bc = 984091.9263194444
    assert jd_bc == convert.struct_time_to_jd(st_bc)


def test_jd_to_struct_time():
    jd_ad = 2458227.9263194446
    st_ad = struct_time([2018, 4, 19] + [10, 13, 54] + convert.TIME_EMPTY_EXTRAS)
    assert st_ad == convert.jd_to_struct_time(jd_ad)
    jd_bc = 984091.9263194444
    st_bc = struct_time([-2018, 4, 19] + [10, 13, 54 - 1] + convert.TIME_EMPTY_EXTRAS)
    assert st_bc == convert.jd_to_struct_time(jd_bc)


def test_jd_round_trip_for_extreme_future():
    original_st = struct_time([999999, 8, 4] + [21, 15, 3] + convert.TIME_EMPTY_EXTRAS)
    jd = convert.struct_time_to_jd(original_st)
    converted_st = convert.jd_to_struct_time(jd)
    assert original_st[:5] == converted_st[:5]
    assert converted_st[5] == 3 - 1


def test_jd_round_trip_for_extreme_past():
    original_st = struct_time([-999999, 8, 4] + [21, 15, 3] + convert.TIME_EMPTY_EXTRAS)
    converted_st = convert.jd_to_struct_time(convert.struct_time_to_jd(original_st))
    assert tuple(converted_st) == (-999999 + 1, 8, 4, 21, 15, 3, 0, 0, -1)


def test_jd_round_trip_for_zero_year_aka_1_bc():
    original_st = struct_time([0, 9, 5] + [4, 58, 59] + convert.TIME_EMPTY_EXTRAS)
    converted_st = convert.jd_to_struct_time(convert.struct_time_to_jd(original_st))
    assert tuple(converted_st) == (0, 9, 5, 4, 58, 59, 0, 0, -1)


def test_jd_round_trip_for_2_bc():
    original_st = struct_time([-1, 12, 5] + [4, 58, 59] + convert.TIME_EMPTY_EXTRAS)
    converted_st = convert.jd_to_struct_time(convert.struct_time_to_jd(original_st))
    assert tuple(converted_st) == (-1, 12, 5, 4, 58, 59, 0, 0, -1)


def test_roll_negative_time_fields():
    year = -100
    month = -17
    day = -34
    hour = -25
    minute = -74
    second = -253
    assert convert._roll_negative_time_fields(
        year, month, day, hour, minute, second
    ) == (-102, 5, 24, 21, 41, 47)

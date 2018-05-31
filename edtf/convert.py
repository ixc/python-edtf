from time import struct_time
from datetime import date, datetime

from edtf import jdutil


TIME_EMPTY_TIME = [0, 0, 0]  # tm_hour, tm_min, tm_sec
TIME_EMPTY_EXTRAS = [0, 0, -1]  # tm_wday, tm_yday, tm_isdst


def dt_to_struct_time(dt):
    """
    Convert a `datetime.date` or `datetime.datetime` to a `struct_time`
    representation *with zero values* for data fields that we cannot always
    rely on for ancient or far-future dates: tm_wday, tm_yday, tm_isdst

    NOTE: If it wasn't for the requirement that the extra fields are unset
    we could use the `timetuple()` method instead of this function.
    """
    if isinstance(dt, datetime):
        return struct_time(
            [dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second] +
            TIME_EMPTY_EXTRAS
        )
    elif isinstance(dt, date):
        return struct_time(
            [dt.year, dt.month, dt.day] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS
        )
    else:
        raise NotImplementedError(
            "Cannot convert %s to `struct_time`" % type(dt))


def struct_time_to_date(st):
    """
    Return a `datetime.date` representing the provided `struct_time.

    WARNING: This will fail for dates with years before 1 AD or after 9999 AD.
    """
    return date(*st[:3])


def struct_time_to_datetime(st):
    """
    Return a `datetime.datetime` representing the provided `struct_time.

    WARNING: This will fail for dates with years before 1 AD or after 9999 AD.
    """
    return datetime(*st[:6])


def trim_struct_time(st, strip_time=False):
    """
    Return a `struct_time` based on the one provided but with the extra fields
    `tm_wday`, `tm_yday`, and `tm_isdst` reset to default values.

    If `strip_time` is set to true the time value are also set to zero:
    `tm_hour`, `tm_min`, and `tm_sec`.
    """
    if strip_time:
        return struct_time(list(st[:3]) + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS)
    else:
        return struct_time(list(st[:6]) + TIME_EMPTY_EXTRAS)


def struct_time_to_jd(st):
    """
    Return a float number representing the Julian Date for the given
    `struct_time`.

    NOTE: extra fields `tm_wday`, `tm_yday`, and `tm_isdst` are ignored.
    """
    year, month, day = st[:3]
    hours, minutes, seconds = st[3:6]

    # Convert time of day to fraction of day
    day += jdutil.hmsm_to_days(hours, minutes, seconds)

    return jdutil.date_to_jd(year, month, day)


def jd_to_struct_time(jd):
    """
    Return a `struct_time` converted from a Julian Date float number.

    WARNING: Conversion to then from Julian Date value to `struct_time` can be
    inaccurate and lose or gain time, especially for BC (negative) years.

    NOTE: extra fields `tm_wday`, `tm_yday`, and `tm_isdst` are set to default
    values, not real ones.
    """
    year, month, day = jdutil.jd_to_date(jd)

    # Convert time of day from fraction of day
    day_fraction = day - int(day)
    hour, minute, second, ms = jdutil.days_to_hmsm(day_fraction)
    day = int(day)

    # This conversion can return negative values for items we do not want to be
    # negative: month, day, hour, minute, second.
    year, month, day, hour, minute, second = _roll_negative_time_fields(
        year, month, day, hour, minute, second)

    return struct_time(
        [year, month, day, hour, minute, second] + TIME_EMPTY_EXTRAS
    )


def _roll_negative_time_fields(year, month, day, hour, minute, second):
    """
    Fix date/time fields which have nonsense negative values for any field
    except for year by rolling the overall date/time value backwards, treating
    negative values as relative offsets of the next higher unit.

    For example minute=5, second=-63 becomes minute=3, second=57 (5 minutes
    less 63 seconds)

    This is very unsophisticated handling of negative values which we would
    ideally do with `dateutil.relativedelta` but cannot because that class does
    not support arbitrary dates, especially not negative years which is the
    only case where these nonsense values are likely to occur anyway.

    NOTE: To greatly simplify the logic we assume all months are 30 days long.
    """
    if second < 0:
        minute += int(second / 60.0)  # Adjust by whole minute in secs
        minute -= 1  # Subtract 1 for negative second
        second %= 60  # Convert negative second to positive remainder
    if minute < 0:
        hour += int(minute / 60.0)  # Adjust by whole hour in minutes
        hour -= 1  # Subtract 1 for negative minutes
        minute %= 60  # Convert negative minute to positive remainder
    if hour < 0:
        day += int(hour / 24.0)  # Adjust by whole day in hours
        day -= 1  # Subtract 1 for negative minutes
        hour %= 24  # Convert negative hour to positive remainder
    if day < 0:
        month += int(day / 30.0)  # Adjust by whole month in days (assume 30)
        month -= 1  # Subtract 1 for negative minutes
        day %= 30  # Convert negative day to positive remainder
    if month < 0:
        year += int(month / 12.0)  # Adjust by whole year in months
        year -= 1  # Subtract 1 for negative minutes
        month %= 12  # Convert negative month to positive remainder
    return (year, month, day, hour, minute, second)

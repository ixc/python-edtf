from time import struct_time
from datetime import date, datetime


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

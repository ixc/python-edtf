import calendar
import re
from time import struct_time
from datetime import date, datetime
from operator import add, sub

from dateutil.relativedelta import relativedelta

from edtf import appsettings
from edtf.convert import dt_to_struct_time, trim_struct_time, \
    TIME_EMPTY_TIME, TIME_EMPTY_EXTRAS

EARLIEST = 'earliest'
LATEST = 'latest'

PRECISION_MILLENIUM = "millenium"
PRECISION_CENTURY = "century"
PRECISION_DECADE = "decade"
PRECISION_YEAR = "year"
PRECISION_MONTH = "month"
PRECISION_SEASON = "season"
PRECISION_DAY = "day"


def days_in_month(year, month):
    """
    Return the number of days in the given year and month, where month is
    1=January to 12=December, and respecting leap years as identified by
    `calendar.isleap()`
    """
    return {
        1: 31,
        2: 29 if calendar.isleap(year) else 28,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31,
    }[month]


def apply_delta(op, time_struct, delta):
    """
    Apply a `relativedelta` to a `struct_time` data structure.

    `op` is an operator function, probably always `add` or `sub`tract to
    correspond to `a_date + a_delta` and `a_date - a_delta`.

    This function is required because we cannot use standard `datetime` module
    objects for conversion when the date/time is, or will become, outside the
    boundary years 1 AD to 9999 AD.
    """
    if not delta:
        return time_struct  # No work to do

    try:
        dt_result = op(datetime(*time_struct[:6]), delta)
        return dt_to_struct_time(dt_result)
    except (OverflowError, ValueError):
        # Year is not within supported 1 to 9999 AD range
        pass

    # Here we fake the year to one in the acceptable range to avoid having to
    # write our own date rolling logic

    # Adjust the year to be close to the 2000 millenium in 1,000 year
    # increments to try and retain accurate relative leap years
    actual_year = time_struct.tm_year
    millenium = int(float(actual_year) / 1000)
    millenium_diff = (2 - millenium) * 1000
    adjusted_year = actual_year + millenium_diff
    # Apply delta to the date/time with adjusted year
    dt = datetime(*(adjusted_year,) + time_struct[1:6])
    dt_result = op(dt, delta)
    # Convert result year back to its original millenium
    final_year = dt_result.year - millenium_diff
    return struct_time(
        (final_year,) + dt_result.timetuple()[1:6] + tuple(TIME_EMPTY_EXTRAS))


class EDTFObject(object):
    """
    Object to attact to a parser to become instantiated when the parser
    completes.
    """
    parser = None

    @classmethod
    def set_parser(cls, p):
        cls.parser = p
        p.addParseAction(cls.parse_action)

    @classmethod
    def parse_action(cls, toks):
        kwargs = toks.asDict()
        try:
            return cls(**kwargs) # replace the token list with the class
        except Exception as e:
            print("trying to %s.__init__(**%s)" % (cls.__name__, kwargs))
            raise e

    @classmethod
    def parse(cls, s):
        return cls.parser.parseString(s)[0]

    def __repr__(self):
        return "%s: '%s'" % (type(self).__name__, str(self))

    def __init__(self, *args, **kwargs):
        str = "%s.__init__(*%s, **%s)" % (
            type(self).__name__,
            args, kwargs,
        )
        raise NotImplementedError("%s is not implemented." % str)

    def __str__(self):
        raise NotImplementedError

    def _strict_date(self, lean):
        raise NotImplementedError

    def lower_strict(self):
        return self._strict_date(lean=EARLIEST)

    def upper_strict(self):
        return self._strict_date(lean=LATEST)

    def _get_fuzzy_padding(self, lean):
        """
        Subclasses should override this to pad based on how precise they are.
        """
        return relativedelta(0)

    def get_is_approximate(self):
        return getattr(self, '_is_approximate', False)

    def set_is_approximate(self, val):
        self._is_approximate = val
    is_approximate = property(get_is_approximate, set_is_approximate)

    def get_is_uncertain(self):
        return getattr(self, '_is_uncertain', False)

    def set_is_uncertain(self, val):
        self._is_uncertain = val
    is_uncertain = property(get_is_uncertain, set_is_uncertain)

    def lower_fuzzy(self):
        strict_val = self.lower_strict()
        return apply_delta(sub, strict_val, self._get_fuzzy_padding(EARLIEST))

    def upper_fuzzy(self):
        strict_val = self.upper_strict()
        return apply_delta(add, strict_val, self._get_fuzzy_padding(LATEST))

    def __eq__(self, other):
        if isinstance(other, EDTFObject):
            return str(self) == str(other)
        elif isinstance(other, date):
            return str(self) == other.isoformat()
        elif isinstance(other, struct_time):
            return self._strict_date() == trim_struct_time(other)
        return False

    def __ne__(self, other):
        if isinstance(other, EDTFObject):
            return str(self) != str(other)
        elif isinstance(other, date):
            return str(self) != other.isoformat()
        elif isinstance(other, struct_time):
            return self._strict_date() != trim_struct_time(other)
        return True

    def __gt__(self, other):
        if isinstance(other, EDTFObject):
            return self.lower_strict() > other.lower_strict()
        elif isinstance(other, date):
            return self.lower_strict() > dt_to_struct_time(other)
        elif isinstance(other, struct_time):
            return self.lower_strict() > trim_struct_time(other)
        raise TypeError("can't compare %s with %s" % (type(self).__name__, type(other).__name__))

    def __ge__(self, other):
        if isinstance(other, EDTFObject):
            return self.lower_strict() >= other.lower_strict()
        elif isinstance(other, date):
            return self.lower_strict() >= dt_to_struct_time(other)
        elif isinstance(other, struct_time):
            return self.lower_strict() >= trim_struct_time(other)
        raise TypeError("can't compare %s with %s" % (type(self).__name__, type(other).__name__))

    def __lt__(self, other):
        if isinstance(other, EDTFObject):
            return self.lower_strict() < other.lower_strict()
        elif isinstance(other, date):
            return self.lower_strict() < dt_to_struct_time(other)
        elif isinstance(other, struct_time):
            return self.lower_strict() < trim_struct_time(other)
        raise TypeError("can't compare %s with %s" % (type(self).__name__, type(other).__name__))

    def __le__(self, other):
        if isinstance(other, EDTFObject):
            return self.lower_strict() <= other.lower_strict()
        elif isinstance(other, date):
            return self.lower_strict() <= dt_to_struct_time(other)
        elif isinstance(other, struct_time):
            return self.lower_strict() <= trim_struct_time(other)
        raise TypeError("can't compare %s with %s" % (type(self).__name__, type(other).__name__))


# (* ************************** Level 0 *************************** *)

class Date(EDTFObject):

    def set_year(self, y):
        if y is None:
            raise AttributeError("Year must not be None")
        self._year = y

    def get_year(self):
        return self._year
    year = property(get_year, set_year)

    def set_month(self, m):
        self._month = m
        if m == None:
            self.day = None

    def get_month(self):
        return self._month
    month = property(get_month, set_month)

    def __init__(self, year=None, month=None, day=None, **kwargs):
        for param in ('date', 'lower', 'upper'):
            if param in kwargs:
                self.__init__(**kwargs[param])
                return

        self.year = year # Year is required, but sometimes passed in as a 'date' dict.
        self.month = month
        self.day = day

    def __str__(self):
        r = self.year
        if self.month:
            r += "-%s" % self.month
            if self.day:
                r += "-%s" % self.day
        return r

    def isoformat(self, default=date.max):
        return "%s-%02d-%02d" % (
            self.year,
            int(self.month or default.month),
            int(self.day or default.day),
        )

    def _precise_year(self, lean):
        # Replace any ambiguous characters in the year string with 0s or 9s
        if lean == EARLIEST:
            return int(re.sub(r'[xu]', r'0', self.year))
        else:
            return int(re.sub(r'[xu]', r'9', self.year))

    def _precise_month(self, lean):
        if self.month and self.month != "uu":
            try:
                return int(self.month)
            except ValueError as e:
                raise ValueError("Couldn't convert %s to int (in %s)" % (self.month, self))
        else:
            return 1 if lean == EARLIEST else 12

    def _precise_day(self, lean):
        if not self.day or self.day == 'uu':
            if lean == EARLIEST:
                return 1
            else:
                return days_in_month(
                    self._precise_year(LATEST), self._precise_month(LATEST)
                )
        else:
            return int(self.day)

    def _strict_date(self, lean):
        """
        Return a `time.struct_time` representation of the date.
        """
        return struct_time(
            (
                self._precise_year(lean),
                self._precise_month(lean),
                self._precise_day(lean),
            ) + tuple(TIME_EMPTY_TIME) + tuple(TIME_EMPTY_EXTRAS)
        )

    @property
    def precision(self):
        if self.day:
            return PRECISION_DAY
        if self.month:
            return PRECISION_MONTH
        return PRECISION_YEAR


class DateAndTime(EDTFObject):
    def __init__(self, date, time):
        self.date = date
        self.time = time

    def __str__(self):
        return self.isoformat()

    def isoformat(self):
        return self.date.isoformat() + "T" + self.time

    def _strict_date(self, lean):
        return self.date._strict_date(lean)

    def __eq__(self, other):
        if isinstance(other, datetime):
            return self.isoformat() == other.isoformat()
        elif isinstance(other, struct_time):
            return self._strict_date() == trim_struct_time(other)
        return super(DateAndTime, self).__eq__(other)

    def __ne__(self, other):
        if isinstance(other, datetime):
            return self.isoformat() != other.isoformat()
        elif isinstance(other, struct_time):
            return self._strict_date() != trim_struct_time(other)
        return super(DateAndTime, self).__ne__(other)


class Interval(EDTFObject):
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __str__(self):
        return "%s/%s" % (self.lower, self.upper)

    def _strict_date(self, lean):
        if lean == EARLIEST:
            try:
                r = self.lower._strict_date(lean)
                if r is None:
                    raise AttributeError
                return r
            except AttributeError: # it's a string, or no date. Result depends on the upper date
                upper = self.upper._strict_date(LATEST)
                return apply_delta(sub, upper, appsettings.DELTA_IF_UNKNOWN)
        else:
            try:
                r = self.upper._strict_date(lean)
                if r is None:
                    raise AttributeError
                return r
            except AttributeError: # an 'unknown' or 'open' string - depends on the lower date
                if self.upper and (self.upper == "open" or self.upper.date == "open"):
                    return dt_to_struct_time(date.today())  # it's still happening
                else:
                    lower = self.lower._strict_date(EARLIEST)
                    return apply_delta(add, lower, appsettings.DELTA_IF_UNKNOWN)


# (* ************************** Level 1 *************************** *)


class UA(EDTFObject):
    @classmethod
    def parse_action(cls, toks):
        args = toks.asList()
        return cls(*args)

    def __init__(self, *args):
        assert len(args)==1
        ua = args[0]

        self.is_uncertain = "?" in ua
        self.is_approximate = "~" in ua

    def __str__(self):
        d = ""
        if self.is_uncertain:
            d += "?"
        if self.is_approximate:
            d += "~"
        return d

    def _get_multiplier(self):
        if self.is_uncertain and self.is_approximate:
            return appsettings.MULTIPLIER_IF_BOTH
        elif self.is_uncertain:
            return appsettings.MULTIPLIER_IF_UNCERTAIN
        elif self.is_approximate:
            return appsettings.MULTIPLIER_IF_APPROXIMATE


class UncertainOrApproximate(EDTFObject):
    def __init__(self, date, ua):
        self.date = date
        self.ua = ua

    def __str__(self):
        if self.ua:
            return "%s%s" % (self.date, self.ua)
        else:
            return str(self.date)

    def _strict_date(self, lean):
        if self.date == "open":
            return dt_to_struct_time(date.today())
        if self.date =="unknown":
            return None # depends on the other date
        return self.date._strict_date(lean)

    def _get_fuzzy_padding(self, lean):
        if not self.ua:
            return relativedelta(0)
        multiplier = self.ua._get_multiplier()

        if self.date.precision == PRECISION_DAY:
            return multiplier * appsettings.PADDING_DAY_PRECISION
        elif self.date.precision == PRECISION_MONTH:
            return multiplier * appsettings.PADDING_MONTH_PRECISION
        elif self.date.precision == PRECISION_YEAR:
            return multiplier * appsettings.PADDING_YEAR_PRECISION


class Unspecified(Date):
    pass


class Level1Interval(Interval):
    def __init__(self, lower, upper):
        self.lower = UncertainOrApproximate(**lower)
        self.upper = UncertainOrApproximate(**upper)

    def _get_fuzzy_padding(self, lean):
        if lean == EARLIEST:
            return self.lower._get_fuzzy_padding(lean)
        elif lean == LATEST:
            return self.upper._get_fuzzy_padding(lean)


class LongYear(EDTFObject):
    def __init__(self, year):
        self.year = year

    def __str__(self):
        return "y%s" % self.year

    def _precise_year(self):
        return int(self.year)

    def _strict_date(self, lean):
        py = self._precise_year()
        if lean == EARLIEST:
            return struct_time(
                [py, 1, 1] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS)
        else:
            return struct_time(
                [py, 12, 31] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS)


class Season(Date):
    def __init__(self, year, season, **kwargs):
        self.year = year
        self.season = season # use season to look up month
        # day isn't part of the 'season' spec, but it helps the inherited
        # `Date` methods do their thing.
        self.day = None

    def __str__(self):
        return "%s-%s" % (self.year, self.season)

    def _precise_month(self, lean):
        rng = appsettings.SEASON_MONTHS_RANGE[int(self.season)]
        if lean == EARLIEST:
            return rng[0]
        else:
            return rng[1]


# (* ************************** Level 2 *************************** *)


class PartialUncertainOrApproximate(Date):

    def set_year(self, y): # Year can be None.
        self._year = y
    year = property(Date.get_year, set_year)

    def __init__(
        self, year=None, month=None, day=None,
        year_ua=False, month_ua = False, day_ua = False,
        year_month_ua = False, month_day_ua = False,
        ssn=None, season_ua=False, all_ua=False
    ):
        self.year = year
        self.month = month
        self.day = day

        self.year_ua = year_ua
        self.month_ua = month_ua
        self.day_ua = day_ua

        self.year_month_ua = year_month_ua
        self.month_day_ua = month_day_ua

        self.season = ssn
        self.season_ua = season_ua

        self.all_ua = all_ua

    def __str__(self):

        if self.season_ua:
            return "%s%s" % (self.season, self.season_ua)

        if self.year_ua:
            y = "%s%s" % (self.year, self.year_ua)
        else:
            y = str(self.year)

        if self.month_ua:
            m = "(%s)%s" % (self.month, self.month_ua)
        else:
            m = str(self.month)

        if self.day:
            if self.day_ua:
                d = "(%s)%s" % (self.day, self.day_ua)
            else:
                d = str(self.day)
        else:
            d = None

        if self.year_month_ua: # year/month approximate. No brackets needed.
            ym = "%s-%s%s" % (y, m, self.year_month_ua)
            if d:
                result = "%s-%s" % (ym, d)
            else:
                result = ym
        elif self.month_day_ua:
            if self.year_ua: # we don't need the brackets round month and day
                result = "%s-%s-%s%s" % (y, m, d, self.month_day_ua)
            else:
                result = "%s-(%s-%s)%s" % (y, m, d, self.month_day_ua)
        else:
            if d:
                result = "%s-%s-%s" % (y, m, d)
            else:
                result = "%s-%s" % (y, m)

        if self.all_ua:
            result = "(%s)%s" % (result, self.all_ua)

        return result

    def _precise_year(self, lean):
        if self.season:
            return self.season._precise_year(lean)
        return super(PartialUncertainOrApproximate, self)._precise_year(lean)

    def _precise_month(self, lean):
        if self.season:
            return self.season._precise_month(lean)
        return super(PartialUncertainOrApproximate, self)._precise_month(lean)

    def _precise_day(self, lean):
        if self.season:
            return self.season._precise_day(lean)
        return super(PartialUncertainOrApproximate, self)._precise_day(lean)

    def _get_fuzzy_padding(self, lean):
        """
        This is not a perfect interpretation as fuzziness is introduced for
        redundant uncertainly modifiers e.g. (2006~)~ will get two sets of
        fuzziness.
        """
        result = relativedelta(0)

        if self.year_ua:
            result += appsettings.PADDING_YEAR_PRECISION * self.year_ua._get_multiplier()
        if self.month_ua:
            result += appsettings.PADDING_MONTH_PRECISION * self.month_ua._get_multiplier()
        if self.day_ua:
            result += appsettings.PADDING_DAY_PRECISION * self.day_ua._get_multiplier()

        if self.year_month_ua:
            result += appsettings.PADDING_YEAR_PRECISION * self.year_month_ua._get_multiplier()
            result += appsettings.PADDING_MONTH_PRECISION * self.year_month_ua._get_multiplier()
        if self.month_day_ua:
            result += appsettings.PADDING_DAY_PRECISION * self.month_day_ua._get_multiplier()
            result += appsettings.PADDING_MONTH_PRECISION * self.month_day_ua._get_multiplier()

        if self.season_ua:
            result += appsettings.PADDING_SEASON_PRECISION * self.season_ua._get_multiplier()

        if self.all_ua:
            multiplier = self.all_ua._get_multiplier()

            if self.precision == PRECISION_DAY:
                result += multiplier * appsettings.PADDING_DAY_PRECISION
                result += multiplier * appsettings.PADDING_MONTH_PRECISION
                result += multiplier * appsettings.PADDING_YEAR_PRECISION
            elif self.precision == PRECISION_MONTH:
                result += multiplier * appsettings.PADDING_MONTH_PRECISION
                result += multiplier * appsettings.PADDING_YEAR_PRECISION
            elif self.precision == PRECISION_YEAR:
                result += multiplier * appsettings.PADDING_YEAR_PRECISION

        return result


class PartialUnspecified(Unspecified):
    pass


class Consecutives(Interval):
    # Treating Consecutive ranges as intervals where one bound is optional
    def __init__(self, lower=None, upper=None):
        if lower and not isinstance(lower, EDTFObject):
            self.lower = Date.parse(lower)
        else:
            self.lower = lower

        if upper and not isinstance(upper, EDTFObject):
            self.upper = Date.parse(upper)
        else:
            self.upper = upper

    def __str__(self):
        return "%s..%s" % (self.lower or '', self.upper or '')


class EarlierConsecutives(Consecutives):
    pass


class LaterConsecutives(Consecutives):
    pass


class OneOfASet(EDTFObject):
    @classmethod
    def parse_action(cls, toks):
        args = [t for t in toks.asList() if isinstance(t, EDTFObject)]
        return cls(*args)

    def __init__(self, *args):
        self.objects = args

    def __str__(self):
        return "[%s]" % (", ".join([str(o) for o in self.objects]))

    def _strict_date(self, lean):
        if lean == LATEST:
            return max([x._strict_date(lean) for x in self.objects])
        else:
            return min([x._strict_date(lean) for x in self.objects])


class MultipleDates(EDTFObject):
    @classmethod
    def parse_action(cls, toks):
        args = [t for t in toks.asList() if isinstance(t, EDTFObject)]
        return cls(*args)

    def __init__(self, *args):
        self.objects = args

    def __str__(self):
        return "{%s}" % (", ".join([str(o) for o in self.objects]))

    def _strict_date(self, lean):
        if lean == LATEST:
            return max([x._strict_date(lean) for x in self.objects])
        else:
            return min([x._strict_date(lean) for x in self.objects])


class MaskedPrecision(Date):
    pass


class Level2Interval(Level1Interval):
    def __init__(self, lower, upper):
        # Check whether incoming lower/upper values are single-item lists, and
        # if so take just the first item. This works around what I *think* is a
        # bug in the grammer that provides us with single-item lists of
        # `PartialUncertainOrApproximate` items for lower/upper values.
        if isinstance(lower, (tuple, list)) and len(lower) == 1:
            self.lower = lower[0]
        else:
            self.lower = lower
        if isinstance(lower, (tuple, list)) and len(upper) == 1:
            self.upper = upper[0]
        else:
            self.upper = upper


class ExponentialYear(LongYear):
    def __init__(self, base, exponent, precision=None):
        self.base = base
        self.exponent = exponent
        self.precision = precision

    def _precise_year(self):
        return int(self.base) * 10 ** int(self.exponent)

    def get_year(self):
        if self.precision:
            return '%se%sp%s' % (self.base, self.exponent, self.precision)
        else:
            return '%se%s' % (self.base, self.exponent)
    year = property(get_year)

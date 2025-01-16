import calendar
import math
import re
from datetime import date, datetime
from operator import add, sub
from time import struct_time
from typing import Optional

from dateutil.relativedelta import relativedelta

from edtf import appsettings
from edtf.convert import (
    TIME_EMPTY_EXTRAS,
    TIME_EMPTY_TIME,
    dt_to_struct_time,
    trim_struct_time,
)

EARLIEST = "earliest"
LATEST = "latest"

PRECISION_MILLENIUM = "millenium"
PRECISION_CENTURY = "century"
PRECISION_DECADE = "decade"
PRECISION_YEAR = "year"
PRECISION_MONTH = "month"
PRECISION_SEASON = "season"
PRECISION_DAY = "day"


def days_in_month(year: int, month: int) -> int:
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
        (final_year,) + dt_result.timetuple()[1:6] + tuple(TIME_EMPTY_EXTRAS)
    )


class EDTFObject:
    """
    Object to attach to a parser to become instantiated when the parser
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
            return cls(**kwargs)  # replace the token list with the class
        except Exception as e:
            print(f"trying to {cls.__name__}.__init__(**{kwargs})")
            raise e

    @classmethod
    def parse(cls, s):
        return cls.parser.parseString(s)[0]

    def __repr__(self):
        return f"{type(self).__name__}: '{str(self)}'"

    def __init__(self, *args, **kwargs):
        str = f"{type(self).__name__}.__init__(*{args}, **{kwargs})"
        raise NotImplementedError(f"{str} is not implemented.")

    def __str__(self):
        raise NotImplementedError

    def _strict_date(self, lean: str = EARLIEST):
        raise NotImplementedError

    def lower_strict(self):
        return self._strict_date(lean=EARLIEST)

    def upper_strict(self):
        return self._strict_date(lean=LATEST)

    def _get_fuzzy_padding(self, lean: str):
        """
        Subclasses should override this to pad based on how precise they are.
        """
        return relativedelta(0)

    def get_is_approximate(self) -> bool:
        return getattr(self, "_is_approximate", False)

    def set_is_approximate(self, val: bool) -> None:
        self._is_approximate = val

    is_approximate = property(get_is_approximate, set_is_approximate)  # noqa

    def get_is_uncertain(self) -> bool:
        return getattr(self, "_is_uncertain", False)

    def set_is_uncertain(self, val: bool) -> None:
        self._is_uncertain = val

    is_uncertain = property(get_is_uncertain, set_is_uncertain)  # noqa

    def get_is_uncertain_and_approximate(self) -> bool:
        return getattr(self, "_uncertain_and_approximate", False)

    def set_is_uncertain_and_approximate(self, val: bool) -> None:
        self._uncertain_and_approximate = val

    is_uncertain_and_approximate = property(
        get_is_uncertain_and_approximate,  # noqa
        set_is_uncertain_and_approximate,  # noqa
    )

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
        raise TypeError(
            f"can't compare {type(self).__name__} with {type(other).__name__}"
        )

    def __ge__(self, other):
        if isinstance(other, EDTFObject):
            return self.lower_strict() >= other.lower_strict()
        elif isinstance(other, date):
            return self.lower_strict() >= dt_to_struct_time(other)
        elif isinstance(other, struct_time):
            return self.lower_strict() >= trim_struct_time(other)
        raise TypeError(
            f"can't compare {type(self).__name__} with {type(other).__name__}"
        )

    def __lt__(self, other):
        if isinstance(other, EDTFObject):
            return self.lower_strict() < other.lower_strict()
        elif isinstance(other, date):
            return self.lower_strict() < dt_to_struct_time(other)
        elif isinstance(other, struct_time):
            return self.lower_strict() < trim_struct_time(other)
        raise TypeError(
            f"can't compare {type(self).__name__} with {type(other).__name__}"
        )

    def __le__(self, other):
        if isinstance(other, EDTFObject):
            return self.lower_strict() <= other.lower_strict()
        elif isinstance(other, date):
            return self.lower_strict() <= dt_to_struct_time(other)
        elif isinstance(other, struct_time):
            return self.lower_strict() <= trim_struct_time(other)
        raise TypeError(
            f"can't compare {type(self).__name__} with {type(other).__name__}"
        )


# (* ************************** Level 0 *************************** *)


class Date(EDTFObject):
    def __init__(  # noqa
        self,
        year: Optional[str] = None,
        month: Optional[str] = None,
        day: Optional[str] = None,
        significant_digits=None,
        **kwargs,
    ):
        for param in ("date", "lower", "upper"):
            if param in kwargs:
                self.__init__(**kwargs[param])
                return

        self._year = year  # Year is required, but sometimes passed in as a 'date' dict.
        self._month = month
        self._day = day
        self.significant_digits = (
            int(significant_digits) if significant_digits else None
        )

    def set_year(self, y: str):
        if y is None:
            raise AttributeError("Year must not be None")
        self._year = y

    def get_year(self) -> str:
        return self._year

    year = property(get_year, set_year)  # noqa

    def set_month(self, m: Optional[str]):
        self._month = m
        if m is None:
            self._day = None

    def get_month(self) -> Optional[str]:
        return self._month

    month = property(get_month, set_month)  # noqa

    def set_day(self, d: Optional[str]):
        self._day = d
        if d is None:
            self._day = None

    def get_day(self) -> Optional[str]:
        return self._day

    day = property(get_day, set_day)  # noqa

    def __str__(self):
        r = self._year
        if self._month:
            r += f"-{self._month}"
            if self._day:
                r += f"-{self._day}"
        if self.significant_digits:
            r += f"S{self.significant_digits}"
        return r

    def isoformat(self, default=date.max):
        return f"{self._year}-{int(self._month or default.month):02d}-{int(self._day or default.day):02d}"

    def lower_fuzzy(self):
        if not hasattr(self, "significant_digits") or not self.significant_digits:
            return apply_delta(
                sub, self.lower_strict(), self._get_fuzzy_padding(EARLIEST)
            )
        else:
            total_digits = len(self._year)
            insignificant_digits = total_digits - self.significant_digits
            lower_year = (
                int(self._year)
                // (10**insignificant_digits)
                * (10**insignificant_digits)
            )
            return struct_time([lower_year, 1, 1] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS)

    def upper_fuzzy(self):
        if not hasattr(self, "significant_digits") or not self.significant_digits:
            return apply_delta(
                add, self.upper_strict(), self._get_fuzzy_padding(LATEST)
            )
        else:
            total_digits = len(self._year)
            insignificant_digits = total_digits - self.significant_digits
            upper_year = (int(self._year) // (10**insignificant_digits) + 1) * (
                10**insignificant_digits
            ) - 1
            return struct_time(
                [upper_year, 12, 31] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS
            )

    def _precise_year(self, lean):
        # Replace any ambiguous characters in the year string with 0s or 9s
        if lean == EARLIEST:
            return int(re.sub(r"X", r"0", self._year))
        else:
            return int(re.sub(r"X", r"9", self._year))

    def _precise_month(self, lean):
        if self._month and self._month != "XX":
            try:
                return int(self._month)
            except ValueError as err:
                raise ValueError(
                    f"Couldn't convert {self._month} to int (in {self})"
                ) from err
        else:
            return 1 if lean == EARLIEST else 12

    def _precise_day(self, lean):
        if not self._day or self._day == "XX":
            if lean == EARLIEST:
                return 1
            else:
                return days_in_month(
                    self._precise_year(LATEST), self._precise_month(LATEST)
                )
        else:
            return int(self._day)

    def _strict_date(self, lean: str = EARLIEST):
        """
        Return a `time.struct_time` representation of the date.
        """
        return struct_time(
            (
                self._precise_year(lean),
                self._precise_month(lean),
                self._precise_day(lean),
            )
            + tuple(TIME_EMPTY_TIME)
            + tuple(TIME_EMPTY_EXTRAS)
        )

    @property
    def precision(self):
        if self._day:
            return PRECISION_DAY
        if self._month:
            return PRECISION_MONTH
        return PRECISION_YEAR

    def estimated(self):
        return self._precise_year(EARLIEST)


class DateAndTime(EDTFObject):
    def __init__(self, date, time):  # noqa: super raises not implemented
        self.date = date
        self.time = time

    def __str__(self):
        return self.isoformat()

    def isoformat(self):
        return self.date.isoformat() + "T" + self.time

    def _strict_date(self, lean: str = EARLIEST):
        return self.date._strict_date(lean)

    def __eq__(self, other):
        if isinstance(other, datetime):
            return self.isoformat() == other.isoformat()
        elif isinstance(other, struct_time):
            return self._strict_date() == trim_struct_time(other)
        return super().__eq__(other)

    def __ne__(self, other):
        if isinstance(other, datetime):
            return self.isoformat() != other.isoformat()
        elif isinstance(other, struct_time):
            return self._strict_date() != trim_struct_time(other)
        return super().__ne__(other)


class Interval(EDTFObject):
    def __init__(self, lower, upper):  # noqa: super() raises not implemented
        self.lower = lower
        self.upper = upper

    def __str__(self):
        return f"{self.lower}/{self.upper}"

    def _strict_date(self, lean: str = EARLIEST):
        if lean == EARLIEST:
            r = self.lower._strict_date(lean)
        else:
            r = self.upper._strict_date(lean)
        return r

    @property
    def precision(self):
        if self.lower.precision == self.upper.precision:
            return self.lower.precision
        return None


# (* ************************** Level 1 *************************** *)


class UA(EDTFObject):
    @classmethod
    def parse_action(cls, toks):
        args = toks.asList()
        return cls(*args)

    def __init__(self, *args):  # noqa: super() raises not implemented
        if len(args) != 1:
            raise AssertionError("UA must have exactly one argument")
        ua = args[0]

        self.is_uncertain = "?" in ua
        self.is_approximate = "~" in ua
        self.is_uncertain_and_approximate = "%" in ua

    def __str__(self):
        d = ""
        if self.is_uncertain:
            d += "?"
        if self.is_approximate:
            d += "~"
        if self.is_uncertain_and_approximate:
            d += "%"
        return d

    def _get_multiplier(self):
        if self.is_uncertain_and_approximate:
            return appsettings.MULTIPLIER_IF_BOTH
        elif self.is_uncertain:
            return appsettings.MULTIPLIER_IF_UNCERTAIN
        elif self.is_approximate:
            return appsettings.MULTIPLIER_IF_APPROXIMATE


class UncertainOrApproximate(EDTFObject):
    def __init__(self, date, ua):  # noqa: super() raises not implemented
        self.date = date
        self.ua = ua
        self.is_uncertain = ua.is_uncertain if ua else False
        self.is_approximate = ua.is_approximate if ua else False
        self.is_uncertain_and_approximate = (
            ua.is_uncertain_and_approximate if ua else False
        )

    def __str__(self):
        if self.ua:
            return f"{self.date}{self.ua}"
        else:
            return str(self.date)

    def _strict_date(self, lean: str = EARLIEST):
        return self.date._strict_date(lean)

    def _get_fuzzy_padding(self, lean):
        if not self.ua:
            return relativedelta()
        multiplier = self.ua._get_multiplier()
        padding = relativedelta()

        # Check the presence of uncertainty on each component
        # self.precision not helpful here:
        # L1 qualified EDTF dates apply qualification across all parts of the date
        if self.date.year:
            padding += relativedelta(
                years=int(multiplier * appsettings.PADDING_YEAR_PRECISION.years)
            )
        if self.date.month:
            padding += relativedelta(
                months=int(multiplier * appsettings.PADDING_MONTH_PRECISION.months)
            )
        if self.date.day:
            padding += relativedelta(
                days=int(multiplier * appsettings.PADDING_DAY_PRECISION.days)
            )

        return padding


class UnspecifiedIntervalSection(EDTFObject):
    def __init__(self, sectionOpen=False, other_section_element=None):  # noqa: super() raises not implemented
        if sectionOpen:
            self.is_open = True
            self.is_unknown = False
        else:
            self.is_open = False
            self.is_unknown = True
        self.other = other_section_element

    def __str__(self):
        if self.is_unknown:
            return ""
        else:
            return ".."

    def _strict_date(self, lean: str = EARLIEST):
        if lean not in (EARLIEST, LATEST):
            raise ValueError("lean must be one of EARLIEST or LATEST")

        if lean == EARLIEST:
            if self.is_unknown:
                upper = self.other._strict_date(LATEST)
                return apply_delta(sub, upper, appsettings.DELTA_IF_UNKNOWN)
            else:
                return -math.inf
        elif lean == LATEST:
            if self.is_unknown:
                lower = self.other._strict_date(EARLIEST)
                return apply_delta(add, lower, appsettings.DELTA_IF_UNKNOWN)
            else:
                return math.inf

    @property
    def precision(self):
        return self.other.date.precision or PRECISION_YEAR


class Unspecified(Date):
    def __init__(
        self,
        year=None,
        month=None,
        day=None,
        significant_digits=None,
        ua=None,
        **kwargs,
    ):
        super().__init__(
            year=year,
            month=month,
            day=day,
            significant_digits=significant_digits,
            **kwargs,
        )
        self.ua = ua
        self.is_uncertain = ua.is_uncertain if ua else False
        self.is_approximate = ua.is_approximate if ua else False
        self.is_uncertain_and_approximate = (
            ua.is_uncertain_and_approximate if ua else False
        )
        self.negative = self.year.startswith("-")

    def __str__(self):
        base = super().__str__()
        if self.ua:
            base += str(self.ua)
        return base

    def _get_fuzzy_padding(self, lean):
        if not self.ua:
            return relativedelta()
        multiplier = self.ua._get_multiplier()
        padding = relativedelta()

        if self.year:
            years_padding = self._years_padding(multiplier)
            padding += years_padding
        if self.month:
            padding += relativedelta(
                months=int(multiplier * appsettings.PADDING_MONTH_PRECISION.months)
            )
        if self.day:
            padding += relativedelta(
                days=int(multiplier * appsettings.PADDING_DAY_PRECISION.days)
            )
        return padding

    def _years_padding(self, multiplier):
        """Calculate year padding based on the precision."""
        precision_settings = {
            PRECISION_MILLENIUM: appsettings.PADDING_MILLENNIUM_PRECISION.years,
            PRECISION_CENTURY: appsettings.PADDING_CENTURY_PRECISION.years,
            PRECISION_DECADE: appsettings.PADDING_DECADE_PRECISION.years,
            PRECISION_YEAR: appsettings.PADDING_YEAR_PRECISION.years,
        }
        years = precision_settings.get(self.precision, 0)
        return relativedelta(years=int(multiplier * years))

    def lower_fuzzy(self):
        strict_val = (
            self.lower_strict()
        )  # negative handled in the lower_strict() override
        adjusted = apply_delta(sub, strict_val, self._get_fuzzy_padding(EARLIEST))
        return adjusted

    def upper_fuzzy(self):
        strict_val = (
            self.upper_strict()
        )  # negative handled in the upper_strict() override

        adjusted = apply_delta(add, strict_val, self._get_fuzzy_padding(LATEST))
        return adjusted

    def lower_strict(self):
        if self.negative:
            strict_val = self._strict_date(
                lean=LATEST
            )  # gets the year right, but need to adjust day and month
            if self.precision in (
                PRECISION_YEAR,
                PRECISION_DECADE,
                PRECISION_CENTURY,
                PRECISION_MILLENIUM,
            ):
                return struct_time(
                    (strict_val.tm_year, 1, 1)
                    + tuple(TIME_EMPTY_TIME)
                    + tuple(TIME_EMPTY_EXTRAS)
                )
            elif self.precision == PRECISION_MONTH:
                return struct_time(
                    (strict_val.tm_year, strict_val.tm_mon, 1)
                    + tuple(TIME_EMPTY_TIME)
                    + tuple(TIME_EMPTY_EXTRAS)
                )
            else:
                return strict_val
        else:
            return self._strict_date(lean=EARLIEST)

    def upper_strict(self):
        if self.negative:
            strict_val = self._strict_date(lean=EARLIEST)
            if self.precision in (
                PRECISION_YEAR,
                PRECISION_DECADE,
                PRECISION_CENTURY,
                PRECISION_MILLENIUM,
            ):
                return struct_time(
                    (strict_val.tm_year, 12, 31)
                    + tuple(TIME_EMPTY_TIME)
                    + tuple(TIME_EMPTY_EXTRAS)
                )
            elif self.precision == PRECISION_MONTH:
                days_in_month = calendar.monthrange(
                    strict_val.tm_year, strict_val.tm_mon
                )[1]
                return struct_time(
                    (strict_val.tm_year, strict_val.tm_mon, days_in_month)
                    + tuple(TIME_EMPTY_TIME)
                    + tuple(TIME_EMPTY_EXTRAS)
                )
            else:
                return strict_val
        else:
            return self._strict_date(lean=LATEST)

    @property
    def precision(self):
        if self.day:
            return PRECISION_DAY
        if self.month:
            return PRECISION_MONTH
        if self.year:
            year_no_symbol = self.year.lstrip("-")
            if year_no_symbol.isdigit():
                return PRECISION_YEAR
            if len(year_no_symbol) == 4 and year_no_symbol.endswith("XXX"):
                return PRECISION_MILLENIUM
            if len(year_no_symbol) == 4 and year_no_symbol.endswith("XX"):
                return PRECISION_CENTURY
            if len(year_no_symbol) == 4 and year_no_symbol.endswith("X"):
                return PRECISION_DECADE
        raise ValueError(f"Unspecified date {self} has no precision")


class Level1Interval(Interval):
    def __init__(self, lower: Optional[dict] = None, upper: Optional[dict] = None):  # noqa
        if lower:
            if lower["date"] == "..":
                self.lower = UnspecifiedIntervalSection(
                    True, UncertainOrApproximate(**upper)
                )
            else:
                self.lower = UncertainOrApproximate(**lower)
        else:
            self.lower = UnspecifiedIntervalSection(
                False, UncertainOrApproximate(**upper)
            )
        if upper:
            if upper["date"] == "..":
                self.upper = UnspecifiedIntervalSection(
                    True, UncertainOrApproximate(**lower)
                )
            else:
                self.upper = UncertainOrApproximate(**upper)
        else:
            self.upper = UnspecifiedIntervalSection(
                False, UncertainOrApproximate(**lower)
            )
        self.is_approximate: bool = (
            self.lower.is_approximate or self.upper.is_approximate
        )
        self.is_uncertain: bool = self.lower.is_uncertain or self.upper.is_uncertain
        self.is_uncertain_and_approximate = (
            self.lower.is_uncertain_and_approximate
            or self.upper.is_uncertain_and_approximate
        )

    def _get_fuzzy_padding(self, lean):
        if lean == EARLIEST:
            return self.lower._get_fuzzy_padding(lean)
        elif lean == LATEST:
            return self.upper._get_fuzzy_padding(lean)


class LongYear(EDTFObject):
    def __init__(self, year: str, significant_digits: Optional[str] = None):  # noqa
        self.year = year
        self.significant_digits = (
            int(significant_digits) if significant_digits else None
        )

    def __str__(self):
        if self.significant_digits:
            return f"Y{self.year}S{self.significant_digits}"
        else:
            return f"Y{self.year}"

    def _precise_year(self):
        return int(self.year)

    def _strict_date(self, lean: str = EARLIEST):
        py = self._precise_year()
        if lean == EARLIEST:
            return struct_time([py, 1, 1] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS)
        else:
            return struct_time([py, 12, 31] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS)

    def estimated(self):
        return self._precise_year()

    def lower_fuzzy(self):
        full_year = self._precise_year()
        strict_val = self.lower_strict()
        if not self.significant_digits:
            return apply_delta(sub, strict_val, self._get_fuzzy_padding(EARLIEST))
        else:
            insignificant_digits = len(str(full_year)) - int(self.significant_digits)
            if insignificant_digits <= 0:
                return apply_delta(sub, strict_val, self._get_fuzzy_padding(EARLIEST))
            padding_value = 10**insignificant_digits
            sig_digits = full_year // padding_value
            lower_year = sig_digits * padding_value
            return apply_delta(
                sub,
                struct_time([lower_year, 1, 1] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS),
                self._get_fuzzy_padding(EARLIEST),
            )

    def upper_fuzzy(self):
        full_year = self._precise_year()
        strict_val = self.upper_strict()
        if not self.significant_digits:
            return apply_delta(add, strict_val, self._get_fuzzy_padding(LATEST))
        else:
            insignificant_digits = len(str(full_year)) - self.significant_digits
            if insignificant_digits <= 0:
                return apply_delta(add, strict_val, self._get_fuzzy_padding(LATEST))
            padding_value = 10**insignificant_digits
            sig_digits = full_year // padding_value
            upper_year = (sig_digits + 1) * padding_value - 1
            return apply_delta(
                add,
                struct_time([upper_year, 12, 31] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS),
                self._get_fuzzy_padding(LATEST),
            )


class Season(Date):
    def __init__(self, year, season, **kwargs):  # noqa
        self.year = year
        self.season = season  # use season to look up month
        # day isn't part of the 'season' spec, but it helps the inherited
        # `Date` methods do their thing.
        self.day = None

    def __str__(self):
        return f"{self.year}-{self.season}"

    def _precise_month(self, lean):
        rng = appsettings.SEASON_L2_MONTHS_RANGE[int(self.season)]
        if lean == EARLIEST:
            return rng[0]

        return rng[1]


# (* ************************** Level 2 *************************** *)


class PartialUncertainOrApproximate(Date):
    def __init__(  # noqa
        self,
        year=None,
        month=None,
        day=None,
        year_ua=False,
        month_ua=False,
        day_ua=False,
        year_month_ua=False,
        month_day_ua=False,
        ssn=None,
        season_ua=False,
        all_ua=False,
        year_ua_b=False,
    ):
        self.year = year
        self.month = month
        self.day = day

        self.year_ua = year_ua
        self.year_ua_b = year_ua_b
        self.month_ua = month_ua
        self.day_ua = day_ua

        self.year_month_ua = year_month_ua
        self.month_day_ua = month_day_ua

        self.season = ssn
        self.season_ua = season_ua

        self.all_ua = all_ua

        uas = [
            year_ua,
            month_ua,
            day_ua,
            year_month_ua,
            month_day_ua,
            season_ua,
            all_ua,
        ]
        self.is_uncertain = any(
            item.is_uncertain for item in uas if hasattr(item, "is_uncertain")
        )
        self.is_approximate = any(
            item.is_approximate for item in uas if hasattr(item, "is_approximate")
        )
        self.is_uncertain_and_approximate = any(
            item.is_uncertain_and_approximate
            for item in uas
            if hasattr(item, "is_uncertain_and_approximate")
        )

    def __str__(self):
        if self.season_ua:
            return f"{self.season}{self.season_ua}"

        if self.year_ua:
            y = f"{self.year}{self.year_ua}"
        else:
            y = f"{self.year_ua_b}{self.year}" if self.year_ua_b else str(self.year)

        m = f"{self.month_ua}{self.month}" if self.month_ua else str(self.month)

        if self.day:
            d = f"{self.day_ua}{self.day}" if self.day_ua else str(self.day)
        else:
            d = None

        if self.year_month_ua:  # year/month approximate. No brackets needed.
            ym = f"{y}-{m}{self.year_month_ua}"
            result = f"{ym}-{d}" if d else ym
        elif self.month_day_ua:
            if self.year_ua:  # we don't need the brackets round month and day
                result = f"{y}-{m}-{d}{self.month_day_ua}"
            else:
                result = f"{y}-({m}-{d}){self.month_day_ua}"
        else:
            result = f"{y}-{m}-{d}" if d else f"{y}-{m}"

        if self.all_ua:
            result = f"({result}){self.all_ua}"

        return result

    def set_year(self, y):  # Year can be None.
        self._year = y

    year = property(Date.get_year, set_year)  # noqa

    def _precise_year(self, lean: str):
        if self.season:
            return self.season._precise_year(lean)
        return super()._precise_year(lean)

    def _precise_month(self, lean: str):
        if self.season:
            return self.season._precise_month(lean)
        return super()._precise_month(lean)

    def _precise_day(self, lean):
        if self.season:
            return self.season._precise_day(lean)
        return super()._precise_day(lean)

    def _get_fuzzy_padding(self, lean):
        """
        This is not a perfect interpretation as fuzziness is introduced for
        redundant uncertainly modifiers e.g. (2006~)~ will get two sets of
        fuzziness.
        """
        result = relativedelta(0)

        if self.year_ua:
            result += (
                appsettings.PADDING_YEAR_PRECISION * self.year_ua._get_multiplier()
            )
        if self.year_ua_b:
            result += (
                appsettings.PADDING_YEAR_PRECISION * self.year_ua_b._get_multiplier()
            )
        if self.month_ua:
            result += (
                appsettings.PADDING_MONTH_PRECISION * self.month_ua._get_multiplier()
            )
        if self.day_ua:
            result += appsettings.PADDING_DAY_PRECISION * self.day_ua._get_multiplier()

        if self.year_month_ua:
            result += (
                appsettings.PADDING_YEAR_PRECISION
                * self.year_month_ua._get_multiplier()
            )
            result += (
                appsettings.PADDING_MONTH_PRECISION
                * self.year_month_ua._get_multiplier()
            )
        if self.month_day_ua:
            result += (
                appsettings.PADDING_DAY_PRECISION * self.month_day_ua._get_multiplier()
            )
            result += (
                appsettings.PADDING_MONTH_PRECISION
                * self.month_day_ua._get_multiplier()
            )

        if self.season_ua:
            result += (
                appsettings.PADDING_SEASON_PRECISION * self.season_ua._get_multiplier()
            )

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
    def __init__(self, lower=None, upper=None):  # noqa
        if lower and not isinstance(lower, EDTFObject):
            self.lower = Date.parse(lower)
        else:
            self.lower = lower

        if upper and not isinstance(upper, EDTFObject):
            self.upper = Date.parse(upper)
        else:
            self.upper = upper

    def __str__(self):
        return "{}..{}".format(self.lower or "", self.upper or "")


class EarlierConsecutives(Level1Interval):
    def __str__(self):
        return f"{self.lower}{self.upper}"


class LaterConsecutives(Level1Interval):
    def __str__(self):
        return f"{self.lower}{self.upper}"


class OneOfASet(EDTFObject):
    def __init__(self, *args):  # noqa
        self.objects = args

    @classmethod
    def parse_action(cls, toks):
        args = [t for t in toks.asList() if isinstance(t, EDTFObject)]
        return cls(*args)

    def __str__(self):
        repr: str = ", ".join([str(o) for o in self.objects])
        return f"[{repr}]"

    def _strict_date(self, lean: str = EARLIEST):
        strict_dates = [x._strict_date(lean) for x in self.objects]
        # Accounting for possible 'inf' and '-inf' values
        if lean == LATEST:
            if any(isinstance(d, float) and d == float("inf") for d in strict_dates):
                return float("inf")
            else:
                return max(
                    (d for d in strict_dates if not isinstance(d, float)),
                    default=float("inf"),
                )
        else:
            if any(isinstance(d, float) and d == float("-inf") for d in strict_dates):
                return float("-inf")
            else:
                return min(
                    (d for d in strict_dates if not isinstance(d, float)),
                    default=float("-inf"),
                )


class MultipleDates(EDTFObject):
    def __init__(self, *args):  # noqa
        self.objects = args

    @classmethod
    def parse_action(cls, toks):
        args = [t for t in toks.asList() if isinstance(t, EDTFObject)]
        return cls(*args)

    def __str__(self):
        repr: str = ", ".join([str(o) for o in self.objects])
        return f"{{{repr}}}"

    def _strict_date(self, lean: str = EARLIEST):
        if lean == LATEST:
            return max([x._strict_date(lean) for x in self.objects])
        return min([x._strict_date(lean) for x in self.objects])


class Level2Interval(Level1Interval):
    def __init__(self, lower, upper):  # noqa
        # Check whether incoming lower/upper values are single-item lists, and
        # if so take just the first item. This works around what I *think* is a
        # bug in the grammar that provides us with single-item lists of
        # `PartialUncertainOrApproximate` items for lower/upper values.
        if isinstance(lower, (tuple, list)) and len(lower) == 1:
            self.lower = lower[0]
        else:
            self.lower = lower

        if isinstance(lower, (tuple, list)) and len(upper) == 1:
            self.upper = upper[0]
        else:
            self.upper = upper
        self.is_approximate = self.lower.is_approximate or self.upper.is_approximate
        self.is_uncertain = self.lower.is_uncertain or self.upper.is_uncertain
        self.is_uncertain_and_approximate = (
            self.lower.is_uncertain_and_approximate
            or self.upper.is_uncertain_and_approximate
        )


class Level2Season(Season):
    pass


class ExponentialYear(LongYear):
    def __init__(self, base, exponent, significant_digits=None):  # noqa
        self.base = base
        self.exponent = exponent
        self.significant_digits = (
            int(significant_digits) if significant_digits else None
        )

    def _precise_year(self):
        return int(self.base) * 10 ** int(self.exponent)

    def get_year(self) -> str:
        if self.significant_digits:
            return f"{self.base}E{self.exponent}S{self.significant_digits}"
        else:
            return f"{self.base}E{self.exponent}"

    year = property(get_year)  # noqa

    def estimated(self):
        return self._precise_year()
